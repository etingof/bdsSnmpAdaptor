# -*- coding: future_fstrings -*-
#
# This file is part of bdsSnmpAdaptor software.
#
# Copyright (C) 2017-2019, RtBrick Inc
# License: BSD License 2.0
#
import binascii
import struct

from bdssnmpadaptor import if_tools

IFTYPEMAP = {
    1: 6  # ethernet-csmacd(6)
}

IFOPERSTATUSMAP = {
    0: 2,  # down(2)
    1: 1,  # up(1),       -- ready to pass packets
    2: 3,  # testing(3)   -- in some test mode
    3: 3  # testing(3)   -- in some test mode
}

IFMTU_LAMBDA = lambda x: int(
    struct.Struct('<h').unpack(binascii.unhexlify(x))[0])
IFSPEED_LAMBDA = lambda x: int(
    struct.Struct('>f').unpack(binascii.unhexlify(x))[0] / 1000 * 8)


class LldpdGlobalLldpIntfStatus(object):
    """Implement SNMP IF-MIB for LLDP BDS interfaces.

    Populates SNMP managed objects of SNMP `IF-MIB` module from
    `global.lldp.intf.status` BDS table.

    Notes
    -----

    Expected input:

    .. code-block:: json

    {
      "objects": [
        {
          "attribute": {
            "supported_breakout_modes": [
              "4x1G"
            ],
            "configured_layer2_mtu": "dc05",
            "supported_max_layer2_mtu": "f205",
            "supported_min_layer2_mtu": "4000",
            "supported_auto_negotiation": "01",
            "configured_bandwidth": "4e9502f9",
            "default_bandwidth": "4e9502f9",
            "supported_bandwidths": [
              "10.000 Gbps",
              "1.000 Gbps"
            ],
            "interface_name": "ifp-0/0/1",
            "interface_description": "Physical interface #1 from node 0, chip 0",
            "interface_type": "01",
            "bandwidth": "4e9502f9",
            "layer2_mtu": "f205",
            "mac_address": "b86a97a59201",
            "admin_status": "01",
            "link_status": "01"
          },
          "update": true,
          "sequence": 200197
        }
      ]
    }
    """

    @classmethod
    def setOids(cls, oidDb, bdsData, bdsIds, uptime):
        """Populates OID DB with BDS information.

        Takes known objects from JSON document, puts them into
        the OID DB as specific MIB managed objects.

        Args:
            oidDb (OidDb): OID DB instance to work on
            bdsData (dict): BDS information to put into OID DB
            bdsIds (list): list of last known BDS record sequence IDs
            uptime (int): system uptime in hundreds of seconds

        Raises:
            BdsError: on OID DB population error
        """

        newBdsIds = [obj['sequence'] for obj in bdsData['objects']]

        if newBdsIds == bdsIds:
            return

        add = oidDb.add

        for i, bdsJsonObject in enumerate(bdsData['objects']):

            attribute = bdsJsonObject['attribute']

            ifName = attribute['interface_name']
            index = if_tools.ifIndexFromIfName(ifName)

            ifPhysicalLocation = if_tools.stripIfPrefixFromIfName(ifName)

            add('IF-MIB', 'ifIndex', index, value=index)

            add('IF-MIB', 'ifDescr', index, value=ifPhysicalLocation)

            add('IF-MIB', 'ifType', index,
                value=IFTYPEMAP[int(attribute['interface_type'])])

            add('IF-MIB', 'ifMtu', index,
                value=IFMTU_LAMBDA(attribute['layer2_mtu']))

            add('IF-MIB', 'ifSpeed', index,
                value=IFSPEED_LAMBDA(attribute['bandwidth']))

            add('IF-MIB', 'ifPhysAddress', index,
                value=attribute['mac_address'].replace(':', ''))

            add('IF-MIB', 'ifAdminStatus', index,
                value=IFOPERSTATUSMAP[int(attribute['admin_status'])])

            add('IF-MIB', 'ifOperStatus', index,
                value=IFOPERSTATUSMAP[int(attribute['link_status'])])

            if i < len(bdsIds):
                # possible table entry change
                ifLastChange = None if newBdsIds[i] == bdsIds[i] else uptime

            else:
                # initial run or table size change
                ifLastChange = uptime if bdsIds else 0

            add('IF-MIB', 'ifLastChange', index, value=ifLastChange)

        # count *all* IF-MIB interfaces we currently have - some
        # may be contributed by other modules
        ifNumber = len(oidDb.getObjectsByName('IF-MIB', 'ifIndex'))

        add('IF-MIB', 'ifNumber', 0, value=ifNumber)

        add('IF-MIB', 'ifStackLastChange', 0,
            value=uptime if bdsIds else 0)
        add('IF-MIB', 'ifTableLastChange', 0,
            value=uptime if bdsIds else 0)

        bdsIds[:] = newBdsIds
