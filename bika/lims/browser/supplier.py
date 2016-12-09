# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from bika.lims.browser.bika_listing import BikaListingView
from bika.lims.controlpanel.bika_instruments import InstrumentsView
from bika.lims.controlpanel.bika_products import ProductsView
from bika.lims.browser.inventory.orderfolder import OrderFolderView
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from Products.CMFCore.utils import getToolByName
from plone.app.layout.viewlets.common import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getMultiAdapter
from zope.interface import implements
from plone.app.layout.globals.interfaces import IViewView
from bika.lims.utils import to_utf8
from Products.ATContentTypes.utils import DT2dt
from datetime import datetime

from bika.lims.browser.referencesample import ReferenceSamplesView


class SupplierInstrumentsView(InstrumentsView):
    def __init__(self, context, request):
        super(SupplierInstrumentsView, self).__init__(context, request)

    def isItemAllowed(self, obj):
        supp = obj.getRawSupplier() if obj else None
        return supp.UID() == self.context.UID() if supp else False


class SupplierReferenceSamplesView(ReferenceSamplesView):
    def __init__(self, context, request):
        super(SupplierReferenceSamplesView, self).__init__(context, request)
        self.contentFilter['path']['query'] = '/'.join(
            context.getPhysicalPath())
        self.context_actions = {_('Add'):
            {
                'url':
                    'createObject?type_name=ReferenceSample',
                'icon':
                    '++resource++bika.lims.images/add.png'}}
        # Remove the Supplier column from the list
        del self.columns['Supplier']
        for rs in self.review_states:
            rs['columns'] = [col for col in rs['columns'] if col != 'Supplier']


class SupplierProductsView(ProductsView):
    def __init__(self, context, request):
        super(SupplierProductsView, self).__init__(context, request)
        self.context = context
        self.request = request
        self.context_actions = {}
        self.categories = []
        self.do_cats = context.bika_setup.getCategoriseProducts()
        if self.do_cats:
            self.pagesize = 0  # hide batching controls
            self.show_categories = True
            self.expand_all_categories = False
            self.ajax_categories = True
            self.category_index = 'getCategoryTitle'
            for rs in self.review_states:
                if 'columns' in rs and 'Category' in rs['columns']:
                    rs['columns'].remove('Category')

    def folderitems(self):
        items = ProductsView.folderitems(self)
        uidsup = self.context.UID()
        outitems = []
        for x in range(len(items)):
            obj = items[x].get('obj', None)
            for supplier in obj.getSupplier():
                if supplier.UID() == uidsup:
                    cat = obj.getCategoryTitle()
                    if self.do_cats:
                        # category is for bika_listing to groups entries
                        items[x]['category'] = cat
                        if cat not in self.categories:
                            self.categories.append(cat)
                    after_icons = ''
                    if obj.getHazardous():
                        after_icons = ("<img src='++resource++bika.lims.images/"
                                       "hazardous.png' title='Hazardous'>")
                    items[x]['replace'][
                        'Title'] = "<a href='%s'>%s</a>&nbsp;%s" % \
                                   (items[x]['url'], items[x]['Title'],
                                    after_icons)
                    outitems.append(items[x])
        return outitems


class ProductPathBarViewlet(ViewletBase):
    """Viewlet for overriding breadcrumbs in Product View"""

    index = ViewPageTemplateFile('templates/path_bar.pt')

    def update(self):
        super(ProductPathBarViewlet, self).update()
        self.is_rtl = self.portal_state.is_rtl()
        breadcrumbs = getMultiAdapter((self.context, self.request),
                                      name='breadcrumbs_view').breadcrumbs()
        breadcrumbs[2]['absolute_url'] += '/products'
        self.breadcrumbs = breadcrumbs


class SupplierOrdersView(OrderFolderView):
    implements(IViewView)

    def __init__(self, context, request):
        super(SupplierOrdersView, self).__init__(context, request)
        self.contentFilter = {
            'portal_type': 'InventoryOrder',
            'sort_on': 'sortable_title',
            'sort_order': 'reverse',
            'path': {
                'query': '/'.join(context.getPhysicalPath()),
                'level': 0
            }
        }
        self.context_actions = {
            _('Add'): {
                'url': 'createObject?type_name=InventoryOrder',
                'icon': '++resource++bika.lims.images/add.png'
            }
        }


class ContactsView(BikaListingView):
    def __init__(self, context, request):
        super(ContactsView, self).__init__(context, request)
        self.catalog = "portal_catalog"
        self.contentFilter = {
            'portal_type': 'SupplierContact',
            'path': {"query": "/".join(context.getPhysicalPath()),
                     "level": 0}
        }
        self.context_actions = {
            _('Add'): {
                'url': 'createObject?type_name=SupplierContact',
                'icon': '++resource++bika.lims.images/add.png'}
        }
        self.show_table_only = False
        self.show_sort_column = False
        self.show_select_row = False
        self.show_select_column = True
        self.pagesize = 25
        self.icon = self.portal_url + \
                    "/++resource++bika.lims.images/contact_big.png"
        self.title = self.context.translate(_("Contacts"))

        self.columns = {
            'getFullname': {'title': _('Full Name')},
            'getEmailAddress': {'title': _('Email Address')},
            'getBusinessPhone': {'title': _('Business Phone')},
            'getMobilePhone': {'title': _('Mobile Phone')},
            'getFax': {'title': _('Fax')},
        }

        self.review_states = [
            {'id': 'default',
             'title': _('All'),
             'contentFilter': {},
             'columns': ['getFullname',
                         'getEmailAddress',
                         'getBusinessPhone',
                         'getMobilePhone',
                         'getFax']},
        ]

    def folderitems(self):
        items = BikaListingView.folderitems(self)
        for x in range(len(items)):
            if not items[x].has_key('obj'):
                continue
            fullname = "<a href='%s'>%s</a>" % \
                       (items[x]['url'], items[x]['obj'].getFullname())
            items[x]['replace']['getFullname'] = fullname

        return items
