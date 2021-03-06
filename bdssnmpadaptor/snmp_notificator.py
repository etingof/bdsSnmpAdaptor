# -*- coding: future_fstrings -*-
#
# This file is part of bdsSnmpAdaptor software.
#
# Copyright (C) 2017-2019, RtBrick Inc
# License: BSD License 2.0
#
import asyncio
import time

from pysnmp.entity.rfc3413 import ntforg
from pysnmp.proto.rfc1902 import Integer32
from pysnmp.proto.rfc1902 import OctetString
from pysnmp.proto.rfc1902 import TimeTicks
from pysnmp.proto.rfc1902 import Unsigned32
from pysnmp.smi import builder
from pysnmp.smi import compiler
from pysnmp.smi import rfc1902
from pysnmp.smi import view

from bdssnmpadaptor import error
from bdssnmpadaptor import snmp_config
from bdssnmpadaptor.config import loadConfig
from bdssnmpadaptor.log import set_logging


class SnmpNotificationOriginator(object):
    """Send SNMP TRAP messages.

    Runs within asyncio loop, fetches messages from the queue and sends
    them in SNMP TRAP notifications to preconfigured target(s).

    Args:
        args (object): argparse namespace object holding command-line options
        queue (Queue): asyncio `Queue` instance used for fetching notification
            data from
    """

    TARGETS_TAG = 'mgrs'

    def __init__(self, args, queue):
        configDict = loadConfig(args.config)

        self.moduleLogger = set_logging(configDict, __class__.__name__)

        self.moduleLogger.info(f'original configDict: {configDict}')

        self._queue = queue

        # temp lines for graylog client end #
        # configDict['usmUserDataMatrix'] = [ usmUserTuple.strip().split(',')
        # for usmUserTuple in configDict['usmUserTuples'].split(';') if len(usmUserTuple) > 0 ]
        # self.moduleLogger.debug('configDict['usmUserDataMatrix']: {}'.format(configDict['usmUserDataMatrix']))
        # configDict['usmUsers'] = []
        self.moduleLogger.info(f'modified configDict: {configDict}')

        self._snmpEngine = snmp_config.getSnmpEngine(
            engineId=configDict['snmp'].get('engineId'))

        engineBoots = snmp_config.setSnmpEngineBoots(
            self._snmpEngine, configDict.get('stateDir', '.'))

        self._targets = snmp_config.setTrapTypeForTag(self._snmpEngine, self.TARGETS_TAG)

        authEntries = {}

        for snmpVersion, snmpConfigEntries in configDict['snmp'].get(
                'versions', {}).items():

            snmpVersion = str(snmpVersion)

            if snmpVersion in ('1', '2c'):

                for security, snmpConfig in snmpConfigEntries.items():

                    community = snmpConfig['community']

                    authLevel = snmp_config.setCommunity(
                        self._snmpEngine, security, community, version=snmpVersion, tag=self.TARGETS_TAG)

                    self.moduleLogger.info(
                        f'Configuring SNMPv{snmpVersion} security name '
                        f'{security}, community name {community}')

                    authEntries[security] = snmpVersion, authLevel

            elif snmpVersion == '3':

                for security, usmCreds in snmpConfigEntries.get('usmUsers', {}).items():

                    authLevel = snmp_config.setUsmUser(
                        self._snmpEngine, security,
                        usmCreds.get('user'),
                        usmCreds.get('authKey'), usmCreds.get('authProtocol'),
                        usmCreds.get('privKey'), usmCreds.get('privProtocol'))

                    self.moduleLogger.info(
                        f'Configuring SNMPv3 USM security {security}, user '
                        f'{usmCreds.get("user")}, '
                        f'auth {usmCreds.get("authKey")}/{usmCreds.get("authProtocol")}, '
                        f'priv {usmCreds.get("privKey")}/{usmCreds.get("privProtocol")}')

                    authEntries[security] = snmpVersion, authLevel

            else:
                raise error.BdsError(f'Unknown SNMP version {snmpVersion}')

            self._birthday = time.time()

        snmpTrapTargets = configDict['notificator'].get('snmpTrapTargets', {}).items()

        for targetId, (targetName, targetConfig) in enumerate(snmpTrapTargets):

            bind_address = targetConfig.get('bind-address', '0.0.0.0'), 0

            security = targetConfig['security-name']

            transportDomain = snmp_config.setSnmpTransport(
                self._snmpEngine, iface=bind_address, iface_num=targetId)

            transportAddress = (targetConfig['address'],
                                int(targetConfig.get('port', 162)))

            snmp_config.setTrapTargetAddress(
                self._snmpEngine, security, transportDomain, transportAddress,
                tag=self.TARGETS_TAG)

            snmpVersion, authLevel = authEntries[security]

            snmp_config.setTrapVersion(
                self._snmpEngine, security, authLevel, snmpVersion)

            self.moduleLogger.info(
                f'Configuring target #{targetId}, transport domain '
                f'{transportDomain}, destination {transportAddress}, '
                f'bind address {bind_address} using security name {security}')

        self._configureMibObjects(configDict)

        self._ntfOrg = ntforg.NotificationOriginator()

        self._trapCounter = 0

        self.moduleLogger.info(
            f'Running SNMP engine ID {self._snmpEngine}, boots {engineBoots}')

    def _configureMibObjects(self, configDict):

        mibBuilder = builder.MibBuilder()
        mibViewController = view.MibViewController(mibBuilder)

        compiler.addMibCompiler(
            mibBuilder, sources=configDict['snmp'].get('mibs', ()))

        self._sysUpTime = rfc1902.ObjectIdentity(
            'SNMPv2-MIB', 'sysUpTime', 0).resolveWithMib(mibViewController)

        self._snmpTrapOID = rfc1902.ObjectIdentity(
            'SNMPv2-MIB', 'snmpTrapOID', 0).resolveWithMib(mibViewController)

        self._rtbrickSyslogTrap = rfc1902.ObjectIdentity(
            'RTBRICK-SYSLOG-MIB', 'rtbrickSyslogTrap', 1).resolveWithMib(mibViewController)

        self._syslogMsgNumber = rfc1902.ObjectIdentity(
            'RTBRICK-SYSLOG-MIB', 'syslogMsgNumber', 0).resolveWithMib(mibViewController)

        self._syslogMsgFacility = rfc1902.ObjectIdentity(
            'RTBRICK-SYSLOG-MIB', 'syslogMsgFacility', 0).resolveWithMib(mibViewController)

        self._syslogMsgSeverity = rfc1902.ObjectIdentity(
            'RTBRICK-SYSLOG-MIB', 'syslogMsgSeverity', 0).resolveWithMib(mibViewController)

        self._syslogMsgText = rfc1902.ObjectIdentity(
            'RTBRICK-SYSLOG-MIB', 'syslogMsgText', 0).resolveWithMib(mibViewController)

        self.moduleLogger.info(
            f'Notifications will include these SNMP objects: '
            f'{self._sysUpTime}=TimeTicks, '
            f'{self._snmpTrapOID}={self._rtbrickSyslogTrap} '
            f'{self._syslogMsgNumber}=Unsigned32 '
            f'{self._syslogMsgFacility}=OctetString '
            f'{self._syslogMsgSeverity}=Integer32 '
            f'{self._syslogMsgText}=OctetString')

    @asyncio.coroutine
    def sendTrap(self, logRecord):
        """Send BDS log message as SNMP notification.

        Args:
            logRecord (dict): log record data as a Python `dict`
        """
        self.moduleLogger.info(f'sendTrap payload: {logRecord}')

        self._trapCounter += 1

        if self._trapCounter == 0xffffffff:
            self._trapCounter = 0

        try:
            syslogMsgFacility = logRecord['host']

        except KeyError:
            self.moduleLogger.error(
                f'cannot get syslog facility from {logRecord}')
            syslogMsgFacility = 'error'

        try:
            syslogMsgSeverity = logRecord['level']

        except KeyError:
            self.moduleLogger.error(
                f'cannot get syslog severity from {logRecord}')
            syslogMsgSeverity = 0

        try:
            syslogMsgText = logRecord['short_message']

        except KeyError:
            self.moduleLogger.error(
                f'cannot get syslog message text from bdsLogDict '
                f'{logRecord}')

            syslogMsgText = 'error'

        self.moduleLogger.info(
            f'data sendTrap {self._trapCounter} {syslogMsgFacility} '
            f'{syslogMsgSeverity} {syslogMsgText}')

        def cbFun(snmpEngine, sendRequestHandle, errorIndication,
                  errorStatus, errorIndex, varBinds, cbCtx):
            if errorIndication:
                self.moduleLogger.error(
                    f'notification {sendRequestHandle} failed: '
                    f'{errorIndication}')

            else:
                self.moduleLogger.error(
                    f'notification {sendRequestHandle} succeeded')

        uptime = int((time.time() - self._birthday) * 100)

        varBinds = [
            (self._sysUpTime, TimeTicks(uptime)),
            (self._snmpTrapOID, self._rtbrickSyslogTrap),
            (self._syslogMsgNumber, Unsigned32(self._trapCounter)),
            (self._syslogMsgFacility, OctetString(syslogMsgFacility)),
            (self._syslogMsgSeverity, Integer32(syslogMsgSeverity)),
            (self._syslogMsgText, OctetString(syslogMsgText))
        ]

        sendRequestHandle = self._ntfOrg.sendVarBinds(
            self._snmpEngine,
            # Notification targets
            self._targets,
            None, '',  # contextEngineId, contextName
            varBinds,
            cbFun
        )

        self.moduleLogger.info(
            f'notification {sendRequestHandle or ""} submitted')

    @asyncio.coroutine
    def run_forever(self):
        """Pull messages off the queue, send SNMP notifications.

        Endlessly wait on the queue for new messages to appear, pull
        one by one and pass them to SNMP notificator.
        """

        while True:
            logRecord = yield from self._queue.get()

            self.moduleLogger.info(f'new log record: {logRecord}')

            try:
                yield from self.sendTrap(logRecord)

            except Exception as exc:
                self.moduleLogger.error(f'TRAP not sent: {exc}')

