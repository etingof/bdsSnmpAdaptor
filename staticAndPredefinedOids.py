#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of bdsSnmpAdaptor software.
#
# Copyright (C) 2017-2019, RtBrick Inc
# License: BSD License 2.0

import os
import sys
sys.path.insert(0, os.path.abspath('..'))
from bdsMappingFunctions import bdsMappingFunctions
import logging
from oidDb import OidDbItem
import asyncio

class StaticAndPredefinedOids (object):

    """


    """

    @classmethod
    async def setOids(self,targetOidDb,staticOidDict):
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.1.0",
            name="sysContact", pysnmpBaseType="OctetString",
            value= staticOidDict["sysDesc"]))
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.2.0",
            name="sysObjectID", pysnmpBaseType="ObjectIdentifier",
            value=".1.3.6.1.4.1.50058.102.1.1.1.2.1" ))     #FIXME get from BDS entity table
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.3.0",
            name="sysUptime", pysnmpBaseType="TimeTicks",
            value=""))
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.4.0",
            name="sysContact", pysnmpBaseType="OctetString",
            value= staticOidDict["sysContact"]))
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.5.0",
            name="sysName", pysnmpBaseType="OctetString",
            value= staticOidDict["sysName"]))
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.6.0",
            name="sysLocation", pysnmpBaseType="OctetString",
            value= staticOidDict["sysLocation"]))
        targetOidDb.insertOid(newOidItem = OidDbItem(
            bdsMappingFunc = "StaticAndPredefinedOids",
            oid = "1.3.6.1.2.1.1.7.0",
            name="SysServices", pysnmpBaseType="Integer32",
            value=6 ))

        print(f'temp print for engineId: {staticOidDict["engineId"]}')
