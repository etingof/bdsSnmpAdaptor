#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of bdsSnmpAdaptor software.
#
# Copyright (C) 2017-2019, RtBrick Inc
# License: BSD License 2.0
#


class StaticAndPredefinedOids(object):

    SYSTEM_TABLE_COLUMNS = [
        'sysDescr',
        'sysObjectID',
        'sysUpTime',
        'sysContact',
        'sysName',
        'sysLocation',
        'sysServices'
    ]

    ENT_TABLE_COLUMNS = [
        'entPhysicalIndex',
        'entPhysicalDescr',
        'entPhysicalVendorType',
        'entPhysicalContainedIn',
        'entPhysicalClass',
        'entPhysicalParentRelPos',
        'entPhysicalName',
        'entPhysicalHardwareRev',
        'entPhysicalFirmwareRev',
        'entPhysicalSoftwareRev',
        'entPhysicalSerialNum',
        'entPhysicalMfgName',
        'entPhysicalModelName',
        'entPhysicalAlias',
        'entPhysicalAssetID',
        'entPhysicalIsFRU',
        'entPhysicalMfgDate',
        'entPhysicalUris'
    ]

    ENT_PHYSICAL_TABLE = [
        [
            1,  # entPhysicalIndex
            'Rtbrick Fullstack on AS5912-54',
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorType
            0,  # entPhysicalContainedIn
            3,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            'chassis',
            '',
            '',
            '',
            '591654XK1848008',
            'Accton',
            'Edgecore Networks AS5912-54 port 10GB SFP+ plus 6 port QSFP28',
            '5916-54XK-O-AC-F',
            '',
            2,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ],
        [
            2,  # entPhysicalIndex
            'AS5912 Compute Board',
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorType
            1,  # entPhysicalContainedIn
            9,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            'AS5916-54XK',
            'R02A',
            'AS5916 V36 20180815',
            '',
            '591654XK1848017',
            'Accton',
            'Intel(R) Xeon(R) CPU D-1518 @ 2.20GHz',
            'AS5916-54XK',
            '',
            1,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ],
        [
            3,  # entPhysicalIndex
            'PSU-1',  # entPhysicalDescr
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorType
            1,  # entPhysicalContainedIn
            6,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            '',  # entPhysicalName
            '',
            '',
            '',
            'NULL',
            'Accton',
            '',
            '',
            '',
            1,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ],
        [
            4,  # entPhysicalIndex
            'PSU-2',  # entPhysicalDescr
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorType
            1,  # entPhysicalContainedIn
            6,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            '',  # entPhysicalName
            '',
            '',
            '',
            'NULL',
            'Accton',
            '',
            '',
            '',
            1,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ],
        [
            5,  # entPhysicalIndex
            'Chassis Fan - 1',  # entPhysicalDescr
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorTyp
            1,  # entPhysicalContainedIn
            7,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            '',  # entPhysicalName
            '',
            '',
            '',
            'NULL',
            'Accton',
            '',
            '',
            '',
            1,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ],
        [
            6,  # entPhysicalIndex
            'Chassis Fan - 2',  # entPhysicalDescr
            '1.3.6.1.4.1.50058.102.1',  # entPhysicalVendorTyp
            1,  # entPhysicalContainedIn
            7,  # entPhysicalClass
            0,  # entPhysicalParentRelPos
            '',  # entPhysicalName
            '',
            '',
            '',
            'NULL',
            'Accton',
            '',
            '',
            '',
            1,
            '2019-5-26,13:30:15.0,-4:0',
            ''
        ]
    ]

    @classmethod
    def setOids(cls, staticOidDict, targetOidDb,
                lastSequenceNumberList, birthday):

        with targetOidDb.module(__name__) as add:

            for column in cls.SYSTEM_TABLE_COLUMNS:
                add('SNMPv2-MIB', column, 0, value=staticOidDict[column])

            add('HOST-RESOURCES-MIB', 'hrSystemUptime', 0, value=0)

        for i, phyValueList in enumerate(cls.ENT_PHYSICAL_TABLE):

            row = cls.ENT_PHYSICAL_TABLE[i]

            for j, column in enumerate(cls.ENT_TABLE_COLUMNS):
                add('ENTITY-MIB', column, row[0], value=row[j])
