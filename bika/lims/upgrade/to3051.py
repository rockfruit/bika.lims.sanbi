# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from bika.lims.permissions import *
from bika.lims.setuphandlers import BikaGenerator
from bika.lims import logger

def upgrade(tool):
    """ Adding getRawSamplePoint/Type idx to obtain Sample's uid easly
    """
    # Hack prevent out-of-date upgrading
    # Related: PR #1484
    # https://github.com/bikalabs/Bika-LIMS/pull/1484
    from bika.lims.upgrade import skip_pre315
    if skip_pre315(aq_parent(aq_inner(tool))):
        return True

    portal = aq_parent(aq_inner(tool))
    bsc = getToolByName(portal, 'bika_setup_catalog', None)

    if 'getRawSamplePoints' not in bsc.indexes():
        bsc.addIndex('getRawSamplePoints', 'KeywordIndex')
    if 'getRawSampleTypes' not in bsc.indexes():
        bsc.addIndex('getRawSampleTypes', 'KeywordIndex')

    logger.info("Reindex added indexes in bika_setup_catalog")
    bsc.manage_reindexIndex(ids=['getRawSamplePoints', ])
    bsc.manage_reindexIndex(ids=['getRawSampleTypes', ])

    return True
