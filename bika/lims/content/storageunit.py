from AccessControl import ClassSecurityInfo

from Products.ATContentTypes.content import schemata
from Products.Archetypes.public import *
from Products.Archetypes.references import HoldingReference
from Products.CMFCore.utils import getToolByName
from plone.app.folder.folder import ATFolder
from zope.interface import implements

from bika.lims import bikaMessageFactory as _
from bika.lims import config
from bika.lims.browser.storage import getStorageTypes
from bika.lims.content.bikaschema import BikaFolderSchema
from bika.lims.interfaces import IStorageUnit

schema = BikaFolderSchema.copy() + Schema((
    StringField(
        'Temperature',
        widget=StringWidget(
            label=_('Temperature'),
        )
    ),
    ReferenceField(
        'Department',
        allowed_types=('Department',),
        relationship='StorageUnitDepartment',
        vocabulary='getDepartments',
        referenceClass=HoldingReference,
        widget=ReferenceWidget(
            checkbox_bound=0,
            label=_('Department'),
            description=_('The laboratory department'),
        ),
    ),
    TextField(
        'Address',
        default_output_type='text/plain',
        allowable_content_types=('text/plain',),
        widget=TextAreaWidget(
            label=_('Address')
        )
    ),
    ReferenceField(
        'UnitType',
        allowed_types=('StorageType',),
        relationship='StorageUnitType',
        vocabulary='getUnitTypes',
        referenceClass=HoldingReference,
        widget=ReferenceWidget(
            checkbox_bound=0,
            label=_('Unit Types'),
            description=_('Select a storage unit type.'),
        ),
    ),
))

schema['description'].schemata = 'default'
schema['description'].widget.visible = True


class StorageUnit(ATFolder):
    security = ClassSecurityInfo()
    implements(IStorageUnit)
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def getDepartments(self):
        bsc = getToolByName(self, 'bika_setup_catalog')
        result = []
        for r in bsc(portal_type='Department',
                     inactive_state='active'):
            result.append((r.UID, r.Title))
        return DisplayList(result)

    def getDepartmentTitle(self):
        return self.getDepartment() and self.getDepartment().Title() or ''

    def getStorageTypes(self, show_all=False):
        """Return a list of types of storage which are supported here.
        """
        types = getStorageTypes()
        if not show_all:
            types = [x for x in types if x['interface'].providedBy(self)]
        return types

    def getUnitTypes(self):
        """Return the unit storage types
        """
        bsc = getToolByName(self, 'bika_setup_catalog')
        result = []
        for r in bsc(portal_type='StorageType',
                     inactive_state='active'):
            result.append((r.UID, r.Title))
        return DisplayList(result)

    def getHierarchy(self, structure=False, separator='.', fieldname='id'):
        hierarchy = []
        item = self
        while (1):
            try:
                accessor = getattr(item, fieldname).getAccessor()
                val = accessor() if callable(accessor) else accessor
            except AttributeError:
                val = getattr(item, fieldname)
            # Don't report on the /storage folder
            if item.portal_type == 'StorageUnits':
                break
            url = "<a href='%s'>%s</a>" % (item.absolute_url(), val)
            hierarchy.append(url if structure else val)
            item = item.aq_parent
        return separator.join(reversed(hierarchy))

schemata.finalizeATCTSchema(schema, folderish=True, moveDiscussion=False)
registerType(StorageUnit, config.PROJECTNAME)
