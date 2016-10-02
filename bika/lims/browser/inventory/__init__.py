from bika.lims.adapters.referencewidgetvocabulary import DefaultReferenceWidgetVocabulary
from bika.lims.jsonapi import get_include_fields
from bika.lims.jsonapi import load_brain_metadata
from bika.lims.jsonapi import load_field_values
from bika.lims.utils import dicts_to_dict
from bika.lims.interfaces import IOrder
from bika.lims.interfaces import IFieldIcons
from bika.lims.interfaces import IJSONReadExtender
from bika.lims.permissions import *
from bika.lims.workflow import get_workflow_actions
from bika.lims.vocabularies import CatalogVocabulary
from bika.lims.utils import to_utf8
from bika.lims.workflow import doActionFor
from DateTime import DateTime
from Products.Archetypes import PloneMessageFactory as PMF
from plone.app.layout.globals.interfaces import IViewView
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import adapts
from zope.component import getAdapters
from zope.component import queryUtility
from zope.interface import implements

import json

from .workflow import OrderWorkflowAction


class SupplierContactVocabularyFactory(CatalogVocabulary):

    def __call__(self):
        parent = self.context.aq_parent
        return super(SupplierContactVocabularyFactory, self).__call__(
            portal_type='Supplier',
            path={'query': "/".join(parent.getPhysicalPath()),
                  'level': 0}
        )


class mailto_link_from_contacts:

    def __init__(self, context):
        self.context = context

    def __call__(self, field):
        contacts = field.get(self.context)
        if not type(contacts) in (list, tuple):
            contacts = [contacts, ]
        ret = []
        for contact in contacts:
            if contact:
                mailto = "<a href='mailto:%s'>%s</a>" % (
                    contact.getEmailAddress(), contact.getFullname())
            ret.append(mailto)
        return ",".join(ret)

def mailto_link_from_ccemails(ccemails):
    def __init__(self, context):
        self.context = context

    def __call__(self, field):
        ccemails = field.get(self.context)
        addresses = ccemails.split(",")
        ret = []
        for address in addresses:
            mailto = "<a href='mailto:%s'>%s</a>" % (
                address, address)
            ret.append(mailto)
        return ",".join(ret)


def store_item_managed_storage(order, storage, stockitems, num_items, product_name, product_id):
    """Store stock items in storage and set the number of the order's items
    """
    # get available positions
    num_free_positions = storage.getFreePositions()
    if num_items > num_free_positions:
        return 'The number entered for %s is %d but the ' \
               'storage level ( %s ) only has %d spaces.' % (
               product_name, num_items, storage.getHierarchy(), num_free_positions)

    positions = storage.get_free_positions()
    for i, pi in enumerate(stockitems):
        position = positions[i]
        pi.setStorageLocation(position.UID())

        wf_tool = getToolByName(position, 'portal_workflow')
        wf_tool.doActionFor(position, 'occupy')

        for lineitem in order.order_lineitems:
            if lineitem['Product'] == product_id:
                lineitem['Stored'] += 1

    return ''

def store_item_unmanaged_storage(order, storage, stockitems, num_items, product_id):
    """Store stock items in unmanaged storage
    """
    wf_tool = storage.portal_workflow
    review_state = wf_tool.getInfoFor(storage, 'review_state')
    if review_state == 'occupied':
        return 'The storage %s is no more available' % storage.getHierarchy()

    for pi in stockitems:
        pi.setStorageLocation(storage.UID())

        for lineitem in order.order_lineitems:
            if lineitem['Product'] == product_id:
                lineitem['Stored'] += 1


def store_item_storage_unit():
    pass
