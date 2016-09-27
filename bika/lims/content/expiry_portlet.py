from plone.app.portlets.portlets import base
from zope.interface import implements
from bika.lims.interfaces import IExpiryPortlet
from zope.formlib import form
from plone.memoize.instance import memoize
from zope.component import getMultiAdapter
from Products.CMFPlone import PloneMessageFactory as _
from Acquisition import aq_inner
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from datetime import datetime


class Assignment(base.Assignment):
    implements(IExpiryPortlet)

    def __init__(self, count=5):
        self.count = count

    @property
    def title(self):
        return _(u"Items about to Expire")

class AddForm(base.AddForm):
    form_fields = form.Fields(IExpiryPortlet)
    label = _(u"Add Expiry Portlet")
    description = _(u"This portlet displays the stock items about to expire.")

    def create(self, data):
        return Assignment(count=data.get('count', 5))

class EditForm(base.EditForm):
    form_fields = form.Fields(IExpiryPortlet)
    label = _(u"Edit Expiry Portlet")
    description = _(u"This portlet displays the stock items about to expire.")


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('expiry_portlet.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.anonymous = portal_state.anonymous()  # whether or not the current user is Anonymous
        self.portal_url = portal_state.portal_url()  # the URL of the portal object

        # a list of portal types considered "end user" types
        self.typesToShow = portal_state.friendly_types()

        plone_tools = getMultiAdapter((context, self.request), name=u'plone_tools')
        self.catalog = plone_tools.catalog()

    def render(self):
        return self._template()

    @property
    def available(self):
        """Show the portlet only if there are one or more elements."""
        return not self.anonymous and len(self._data())

    def expiry_items(self):
        return self._data()

    def recently_modified_link(self):
        return '%s/recently_modified' % self.portal_url

    def months_between(self,date1,date2):
        if date1>date2:
            date1,date2=date2,date1
        m1=date1.year*12+date1.month
        m2=date2.year*12+date2.month
        months=m2-m1
        if date1.day>date2.day:
            months-=1
        elif date1.day==date2.day:
            seconds1=date1.hour*3600+date1.minute+date1.second
            seconds2=date2.hour*3600+date2.minute+date2.second
            if seconds1>seconds2:
                months-=1
        return months

    @memoize
    def _data(self):
        limit = self.data.count
        ans = self.catalog(portal_type='StockItems',
                            sort_on='modified',
                            sort_order='reverse')
        anss = ans[0].getObject().contentItems()
        ans = []
        context = aq_inner(self.context)
        today = datetime.now()
        for i in anss:
            item = i[1]
            status = context.portal_workflow.getInfoFor(item, 'review_state')            
            if status and status == "valid":
                date1 = datetime.strptime(str(item.getExpiryDate())[0:10], '%Y/%m/%d')
                date2 = datetime.strptime(str(today)[0:10], '%Y-%m-%d')
                # print self.months_between(date1,date2)
                if self.months_between(date1,date2) <= 2:
                    ans.append(item)
        ans = sorted(ans, key=lambda item: item.getExpiryDate())
        if len(ans)>limit:
            self.more_button = True 
        else:
            self.more_button = None
        return ans[:limit]
