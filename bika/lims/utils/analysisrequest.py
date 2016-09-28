# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.CMFCore.utils import getToolByName
from bika.lims.interfaces import ISample, IAnalysisService, IAnalysis
from bika.lims import logger
from bika.lims.utils import tmpID
from bika.lims.utils.sample import create_sample
from bika.lims.utils.samplepartition import create_samplepartition
from Products.CMFCore.WorkflowCore import WorkflowException
from bika.lims.workflow import doActionFor
from plone import api
from Products.CMFPlone.utils import _createObjectByType


def create_analysisrequest(context, request, values, analyses=None,
                           partitions=None, specifications=None, prices=None):
    """This is meant for general use and should do everything necessary to
    create and initialise an AR and any other required auxilliary objects
    (Sample, SamplePartition, Analysis...)

    :param context:
        The container in which the ARs will be created.
    :param request:
        The current Request object.
    :param values:
        a dict, where keys are AR|Sample schema field names.
    :param analyses:
        Analysis services list.  If specified, augments the values in
        values['Analyses']. May consist of service objects, UIDs, or Keywords.
    :param partitions:
        A list of dictionaries, if specific partitions are required.  If not
        specified, AR's sample is created with a single partition.
    :param specifications:
        These values augment those found in values['Specifications']
    :param prices:
        Allow different prices to be set for analyses.  If not set, prices
        are read from the associated analysis service.
    """

    # Gather neccesary tools
    workflow = getToolByName(context, 'portal_workflow')
    bc = getToolByName(context, 'bika_catalog')
    # Analyses are analyses services
    analyses_services = analyses
    analyses = []
    # It's necessary to modify these and we don't want to pollute the
    # parent's data
    values = values.copy()
    analyses_services = analyses_services if analyses_services else []
    anv = values['Analyses'] if values.get('Analyses', None) else []
    analyses_services = anv + analyses_services

    if not analyses_services:
        raise RuntimeError(
                "create_analysisrequest: no analyses services provided")

    # Create new sample or locate the existing for secondary AR
    if not values.get('Sample', False):
        secondary = False
        workflow_enabled = context.bika_setup.getSamplingWorkflowEnabled()
        sample = create_sample(context, request, values)
    else:
        secondary = True
        sample = get_sample_from_values(context, values)
        workflow_enabled = sample.getSamplingWorkflowEnabled()

    # Create the Analysis Request
    ar = _createObjectByType('AnalysisRequest', context, tmpID())

    # Set some required fields manually before processForm is called
    ar.setSample(sample)
    values['Sample'] = sample
    ar.processForm(REQUEST=request, values=values)
    # Object has been renamed
    ar.edit(RequestID=ar.getId())

    # Set initial AR state
    action = '{0}sampling_workflow'.format('' if workflow_enabled else 'no_')
    workflow.doActionFor(ar, action)

    # Set analysis request analyses
    service_uids = _resolve_items_to_service_uids(analyses_services)
    # processForm already has created the analyses, but here we create the
    # analyses with specs and prices. This function, even it is called 'set',
    # deletes the old analyses, so eventually we obtain the desired analyses.
    ar.setAnalyses(service_uids, prices=prices, specs=specifications)
    # Gettin the ar objects
    analyses = ar.getAnalyses(full_objects=True)
    # Continue to set the state of the AR
    skip_receive = ['to_be_sampled', 'sample_due', 'sampled', 'to_be_preserved']
    if secondary:
        # Only 'sample_due' and 'sample_recieved' samples can be selected
        # for secondary analyses
        doActionFor(ar, 'sampled')
        doActionFor(ar, 'sample_due')
        sample_state = workflow.getInfoFor(sample, 'review_state')
        if sample_state not in skip_receive:
            doActionFor(ar, 'receive')

    # Set the state of analyses we created.
    for analysis in analyses:
        doActionFor(analysis, 'sample_due')
        analysis_state = workflow.getInfoFor(analysis, 'review_state')
        if analysis_state not in skip_receive:
            doActionFor(analysis, 'receive')

    if not secondary:
        # Create sample partitions
        if not partitions:
            partitions = [{'services': service_uids}]
        for n, partition in enumerate(partitions):
            # Calculate partition id
            partition_prefix = sample.getId() + "-P"
            partition_id = '%s%s' % (partition_prefix, n + 1)
            partition['part_id'] = partition_id
            # Point to or create sample partition
            if partition_id in sample.objectIds():
                partition['object'] = sample[partition_id]
            else:
                partition['object'] = create_samplepartition(
                    sample,
                    partition,
                    analyses
                )
        # If Preservation is required for some partitions,
        # and the SamplingWorkflow is disabled, we need
        # to transition to to_be_preserved manually.
        if not workflow_enabled:
            to_be_preserved = []
            sample_due = []
            lowest_state = 'sample_due'
            for p in sample.objectValues('SamplePartition'):
                if p.getPreservation():
                    lowest_state = 'to_be_preserved'
                    to_be_preserved.append(p)
                else:
                    sample_due.append(p)
            for p in to_be_preserved:
                doActionFor(p, 'to_be_preserved')
            for p in sample_due:
                doActionFor(p, 'sample_due')
            doActionFor(sample, lowest_state)
            doActionFor(ar, lowest_state)

        # Transition pre-preserved partitions
        for p in partitions:
            if 'prepreserved' in p and p['prepreserved']:
                part = p['object']
                state = workflow.getInfoFor(part, 'review_state')
                if state == 'to_be_preserved':
                    workflow.doActionFor(part, 'preserve')

    # Return the newly created Analysis Request
    return ar

def get_sample_from_values(context, values):
    """values may contain a UID or a direct Sample object.
    """
    if ISample.providedBy(values['Sample']):
        sample = values['Sample']
    else:
        bc = getToolByName(context, 'bika_catalog')
        brains = bc(UID=values['Sample'])
        if brains:
            sample = brains[0].getObject()
        else:
            raise RuntimeError(
                "create_analysisrequest: invalid sample value provided. values=%s" % values)
    if not sample:
        raise RuntimeError(
            "create_analysisrequest: invalid sample value provided. values=%s" % values)


def _resolve_items_to_service_uids(items):
    """ Returns a list of service uids without duplicates based on the items
    :param items:
        A list (or one object) of service-related info items. The list can be
        heterogeneous and each item can be:
        - Analysis Service instance
        - Analysis instance
        - Analysis Service title
        - Analysis Service UID
        - Analysis Service Keyword
        If an item that doesn't match any of the criterias above is found, the
        function will raise a RuntimeError
    """
    portal = None
    bsc = None
    service_uids = []

    # Maybe only a single item was passed
    if type(items) not in (list, tuple):
        items = [items, ]
    for item in items:
        # service objects
        if IAnalysisService.providedBy(item):
            uid = item.UID()
            service_uids.append(uid)
            continue

        # Analysis objects (shortcut for eg copying analyses from other AR)
        if IAnalysis.providedBy(item):
            uid = item.getService().UID()
            service_uids.append(uid)
            continue

        # An object UID already there?
        if (item in service_uids):
            continue

        # Maybe object UID.
        portal = portal if portal else api.portal.get()
        bsc = bsc if bsc else getToolByName(portal, 'bika_setup_catalog')
        brains = bsc(UID=item)
        if brains:
            uid = brains[0].UID
            service_uids.append(uid)
            continue

        # Maybe service Title
        brains = bsc(portal_type='AnalysisService', title=item)
        if brains:
            uid = brains[0].UID
            service_uids.append(uid)
            continue

        # Maybe service Keyword
        brains = bsc(portal_type='AnalysisService', getKeyword=item)
        if brains:
            uid = brains[0].UID
            service_uids.append(uid)
            continue

        raise RuntimeError(
            str(item) + " should be the UID, title, keyword "
                        " or title of an AnalysisService.")

    return list(set(service_uids))
