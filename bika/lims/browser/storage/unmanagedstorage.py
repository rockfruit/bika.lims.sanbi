from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.layout.globals.interfaces import IViewView
from zope.interface.declarations import implements

from bika.lims import bikaMessageFactory as _
from bika.lims.browser.bika_listing import BikaListingView


class UnmanagedStorageView(BikaListingView):
    """This is the default view for Unmanaged storage.
    """
    template = ViewPageTemplateFile("managedstorage_view.pt")

    def __init__(self, context, request):
        super(UnmanagedStorageView, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):

        StoredItems = StoredItemsView(self.context, self.request)
        self.stored_items_table = StoredItems.contents_table(table_only=True)

        return self.template()

class StoredItemsView(BikaListingView):
    """This listing shows all items which are stored here.
    """

    implements(IFolderContentsView, IViewView)

    def __init__(self, context, request):
        super(StoredItemsView, self).__init__(context, request)

        self.context = context
        self.request = request
        self.catalog = 'bika_setup_catalog'
        path = '/'.join(context.getPhysicalPath())
        self.contentFilter = {}
        self.context_actions = {}
        self.title = ''
        self.description = ''
        self.icon = ''
        self.show_sort_column = False
        self.show_select_row = False
        self.show_select_column = True
        self.pagesize = 25
        self.columns = {
            'ItemID': {'title': _('Item ID'), 'index': 'id'},
            'ItemTitle': {'title': _('Item Title'), 'index': 'sortable_title'},
            'ItemType': {'title': _('Item Type'), 'index': 'Type'},
            'review_state': {'title': _('State'), 'toggle': True},
        }

        self.review_states = [
            {'id': 'default',
             'title': _('Active'),
             'contentFilter': {'inactive_state': 'active'},
             'transitions': [{'id': 'deactivate'}, ],
             'columns': ['ItemID',
                         'ItemTitle',
                         'ItemType',
                         'review_state']},
            {'id': 'all',
             'title': _('All'),
             'contentFilter': {},
             'columns': ['ItemID',
                         'ItemTitle',
                         'ItemType',
                         'review_state']},
        ]

    def folderitems(self, full_objects=False):
        items = BikaListingView.folderitems(self)
        for x in range(len(items)):
            obj = items[x]['obj']
            items[x]['ItemID'] = obj.getId()
            items[x]['ItemTitle'] = obj.Title()
            items[x]['ItemType'] = obj.portal_type
            items[x]['Location'] = obj.getHierarchy()
            items[x]['replace']['Title'] = \
                "<a href='%s'>%s</a>" % (items[x]['url'], items[x]['Title'])
            stitles = [s['title'] for s in obj.getStorageTypes()]
            items[x]['StorageTypes'] = ','.join(stitles)
        return items

    def contentsMethod(self, contentFilter):
        return self.context.getBackRefs("ItemStorageLocation")
