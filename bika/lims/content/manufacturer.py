from AccessControl import ClassSecurityInfo

from Products.Archetypes.public import *
from zope.interface import implements

from bika.lims.config import PROJECTNAME
from bika.lims.content.bikaschema import BikaSchema
from bika.lims.interfaces import IManufacturer

schema = BikaSchema.copy()

schema['description'].schemata = 'default'
schema['description'].widget.visible = True


class Manufacturer(BaseContent):
    implements(IManufacturer)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)


registerType(Manufacturer, PROJECTNAME)
