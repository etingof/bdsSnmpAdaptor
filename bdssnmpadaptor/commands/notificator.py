#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of bdsSnmpAdaptor software.
#
# Copyright (C) 2017-2019, RtBrick Inc
# License: BSD License 2.0
#
import argparse
import asyncio
import json
import sys
from aiohttp import web

from pysnmp.hlapi.asyncio import CommunityData
from pysnmp.hlapi.asyncio import ContextData
from pysnmp.hlapi.asyncio import NotificationType
from pysnmp.hlapi.asyncio import ObjectIdentity
from pysnmp.hlapi.asyncio import UdpTransportTarget
from pysnmp.hlapi.asyncio import sendNotification
from pysnmp.proto.rfc1902 import Integer32
from pysnmp.proto.rfc1902 import OctetString
from pysnmp.proto.rfc1902 import Unsigned32

from bdssnmpadaptor.config import loadBdsSnmpAdapterConfigFile
from bdssnmpadaptor.log import set_logging
from bdssnmpadaptor import snmp_config

RTBRICKSYSLOGTRAP = "1.3.6.1.4.1.50058.103.1.1"
SYSLOGMSG = "1.3.6.1.4.1.50058.102.1.1.0"
SYSLOGMSGNUMBER = "1.3.6.1.4.1.50058.102.1.1.1.0"
SYSLOGMSGFACILITY = "1.3.6.1.4.1.50058.102.1.1.2.0"
SYSLOGMSGSEVERITY = "1.3.6.1.4.1.50058.102.1.1.3.0"
SYSLOGMSGTEXT = "1.3.6.1.4.1.50058.102.1.1.4.0"


class AsyncioTrapGenerator(object):

    def __init__(self, cliArgsDict, restHttpServerObj):
        configDict = loadBdsSnmpAdapterConfigFile(
            cliArgsDict["configFile"], "notificator")

        set_logging(configDict,"notificator", self)

        self.moduleLogger.info("original configDict: {}".format(configDict))

        # configDict["usmUserDataMatrix"] = [ usmUserTuple.strip().split(",")
        # for usmUserTuple in configDict["usmUserTuples"].split(';') if len(usmUserTuple) > 0 ]
        # self.moduleLogger.debug("configDict['usmUserDataMatrix']: {}".format(configDict["usmUserDataMatrix"]))
        # configDict["usmUsers"] = []
        self.moduleLogger.info("modified configDict: {}".format(configDict))

        self.snmpEngine = snmp_config.getSnmpEngine(
            engineId=configDict.get('engineId'))

        engineBoots = snmp_config.setSnmpEngineBoots(
            self.snmpEngine, configDict.get('stateDir', '.'))

        self.snmpVersion = configDict["version"]

        if self.snmpVersion == "2c":
            self.community = configDict["community"]

            self.moduleLogger.info(
                "SNMP version {} community {}".format(
                    self.snmpVersion, self.community))
            # config.addV1System(self.snmpEngine, 'my-area', self.community )

        elif self.snmpVersion == "3":
            usmUserDataMatrix = [
                usmUserTuple.strip().split(",")
                for usmUserTuple in configDict["usmUserTuples"].split(';')
                if len(usmUserTuple) > 0]

        self.snmpTrapTargets = configDict["snmpTrapTargets"]
        self.snmpTrapPort = configDict["snmpTrapPort"]
        self.trapCounter = 0

        self.restHttpServerObj = restHttpServerObj

        self.moduleLogger.info('Running SNMP engine ID {}, boots {}'.format(
            self.snmpEngine, engineBoots))

    async def sendTrap(self, bdsLogDict):
        self.moduleLogger.debug(
            "sendTrap bdsLogDict: {}".format(bdsLogDict))

        self.trapCounter += 1

        try:
            syslogMsgFacility = bdsLogDict["host"]

        except Exception as e:
            self.moduleLogger.error(
                "cannot set syslogMsgFacility from bdsLogDict: "
                "{}".format(bdsLogDict, e))
            syslogMsgFacility = "error"

        try:
            syslogMsgSeverity = bdsLogDict["level"]

        except Exception as e:
            self.moduleLogger.error(
                "cannot set syslogMsgSeverity from bdsLogDict: "
                "{}".format(bdsLogDict, e))
            syslogMsgSeverity = 0

        try:
            syslogMsgText = bdsLogDict["full_message"]

        except Exception as e:
            self.moduleLogger.error(
                "connot set syslogMsgText from bdsLogDict: "
                "{}".format(bdsLogDict, e))

            syslogMsgText = "error"

        self.moduleLogger.debug(
            "data sendTrap {} {} {} {}".format(
                self.trapCounter, syslogMsgFacility,
                syslogMsgSeverity, syslogMsgText))

        errorIndication, errorStatus, errorIndex, varBinds = await sendNotification(
            self.snmpEngine,
            CommunityData(self.community, mpModel=1),  # mpModel defines version
            UdpTransportTarget((self.snmpTrapServer, self.snmpTrapPort)),
            ContextData(),
            'trap',
            NotificationType(
                ObjectIdentity(RTBRICKSYSLOGTRAP)
            ).addVarBinds(
                # ('1.3.6.1.6.3.1.1.4.3.0',RTBRICKSYSLOGTRAP),
                (SYSLOGMSGNUMBER, Unsigned32(self.trapCounter)),
                (SYSLOGMSGFACILITY, OctetString(syslogMsgFacility)),
                (SYSLOGMSGSEVERITY, Integer32(syslogMsgSeverity)),
                (SYSLOGMSGTEXT, OctetString(syslogMsgText))
            )
        )
        if errorIndication:
            self.moduleLogger.error(errorIndication)

    async def run_forever(self):

        while True:
            await asyncio.sleep(0.001)
            if len(self.restHttpServerObj.bdsLogsToBeProcessedList) > 0:
                bdsLogToBeProcessed = self.restHttpServerObj.bdsLogsToBeProcessedList.pop(0)

                self.moduleLogger.debug("bdsLogToBeProcessed: {}".format(bdsLogToBeProcessed))

                await self.sendTrap(bdsLogToBeProcessed)

    async def closeSnmpEngine(self):
        self.snmpEngine.transportDispatcher.closeDispatcher()


class AsyncioRestServer(object):

    def __init__(self, cliArgsDict):

        self.moduleFileNameWithoutPy = sys.modules[__name__].__file__.split(".")[0]

        configDict = loadBdsSnmpAdapterConfigFile(cliArgsDict["configFile"], "notificator")
        set_logging(configDict,"notificator", self)
        self.listeningIP =  configDict["listeningIP"]
        self.listeningPort = configDict["listeningPort"]

        self.requestCounter = 0

        self.bdsLogsToBeProcessedList = []
        self.snmpTrapGenerator = AsyncioTrapGenerator(cliArgsDict, self)

    async def handler(self, request):

        """| Coroutine that accepts a Request instance as its only argument.
           | Returnes 200 with a copy of the incoming header dict.

        """
        peerIP = request._transport_peername[0]

        self.requestCounter += 1

        self.moduleLogger.info(
            "handler: incoming request peerIP:{}".format(
                peerIP, request.headers, self.requestCounter))
        # self.moduleLogger.debug ("handler: peerIP:{} headers:{} counter:{}
        # ".format(peerIP,request.headers,self.requestCounter))

        data = {
            'headers': dict(request.headers)
        }

        jsonTxt = await request.text()  #

        try:
            bdsLogDict = json.loads(jsonTxt)

        except Exception as e:
            self.moduleLogger.error(
                "connot convert json to dict:{} {}".format(jsonTxt, e))

        else:
            self.bdsLogsToBeProcessedList.append(bdsLogDict)
            # await self.snmpTrapGenerator.sendTrap(bdsLogDict)

        return web.json_response(data)

    async def backgroundLogging(self):
        while True:
            self.moduleLogger.debug(
                "restServer Running - process list length: {}".format(
                    len(self.bdsLogsToBeProcessedList)))
            await asyncio.sleep(1)

    async def run_forever(self):
        server = web.Server(self.handler)
        runner = web.ServerRunner(server)

        await runner.setup()

        site = web.TCPSite(runner, self.listeningIP, self.listeningPort)

        await site.start()

        await asyncio.gather(
            self.snmpTrapGenerator.run_forever(),
            self.backgroundLogging()
        )


def main():

    epilogTXT = """

    ... to be added """

    parser = argparse.ArgumentParser(
        epilog=epilogTXT, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument(
        "-f", "--configFile", default="./bdsSnmpTrapAdaptor.yml", type=str,
        help="config file")

    cliargs = parser.parse_args()
    cliArgsDict = vars(cliargs)

    myRestHttpServer = AsyncioRestServer(cliArgsDict)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(myRestHttpServer.run_forever())

    except KeyboardInterrupt:
        pass

    loop.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
