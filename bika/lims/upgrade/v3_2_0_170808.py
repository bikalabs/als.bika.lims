# -*- coding: utf-8 -*-
#
#  This file is part of Bika LIMS
#
# Copyright 2011-2017 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
from Acquisition import aq_inner
from Acquisition import aq_parent
from math import floor

from bika.lims import logger
from bika.lims.upgrade import upgradestep
from bika.lims.upgrade.utils import UpgradeUtils

product = 'bika.lims'
version = '3.2.0.170808'


@upgradestep(product, version)
def upgrade(tool):
    portal = aq_parent(aq_inner(tool))
    ut = UpgradeUtils(portal)
    ufrom = ut.getInstalledVersion(product)
    if ut.isOlderVersion(product, version):
        logger.info('Skipping upgrade of {0}: {1} > {2}'.format(
            product, ufrom, version))
        # The currently installed version is more recent than the target
        # version of this upgradestep
        return True

    logger.info('Upgrading {0}: {1} -> {2}'.format(product, ufrom, version))

    an143_stringfield_ldl_udl(portal)

    # Refresh affected catalogs
    ut.refreshCatalogs()

    logger.info('{0} upgraded to version {1}'.format(product, version))
    return True


def an143_stringfield_ldl_udl(portal):
    """LDL and UDL on AS were FixedPoint fields.  They must be
    converted to String values now.  This routine will remove trailing
    decimal zeroes and entire decimal portion in case of ".0".
    """
    brains = portal.bika_setup_catalog(portal_type='AnalysisService')
    services = (b.getObject() for b in brains)
    for service in services:
        # LDL
        _ldl = service.Schema()['LowerDetectionLimit'].get(service)
        if isinstance(_ldl, tuple):
            ldl = float("{}.{}".format(*_ldl))
            if ldl == floor(ldl):
                ldl = int(ldl)
            ldl = str(ldl)
            logger.info("{} LDL was {}, now set to '{}'".format(
                service.Title(), _ldl, ldl))
            service.setLowerDetectionLimit(ldl)
        # UDL
        _udl = service.Schema()['UpperDetectionLimit'].get(service)
        if isinstance(_udl, tuple):
            udl = float("{}.{}".format(*_udl))
            if udl == floor(udl):
                udl = int(udl)
            udl = str(udl)
            logger.info("{} UDL was {}, now set to '{}'".format(
                service.Title(), _udl, udl))
            service.setUpperDetectionLimit(udl)
