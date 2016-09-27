"""Product Category

Category of the product, for example, sampling containers and sampling
kits.
"""
from AccessControl import ClassSecurityInfo
from bika.lims.config import PROJECTNAME
from bika.lims import bikaMessageFactory as _
from bika.lims.content.bikaschema import BikaSchema
from bika.lims.interfaces import IProductCategory
from Products.Archetypes.public import *
from zope.interface import implements

schema = BikaSchema.copy() + Schema((
    StringField('Prefix',
        required=True,
        widget=StringWidget(
            label=_("Product Category Prefix"),
        ),
    ),
))

schema['description'].widget.visible = True
schema['description'].schemata = 'default'

class ProductCategory(BaseContent):
    implements(IProductCategory)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

registerType(ProductCategory, PROJECTNAME)