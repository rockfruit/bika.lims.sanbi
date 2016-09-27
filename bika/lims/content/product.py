from AccessControl import ClassSecurityInfo
from zope.interface import implements
from bika.lims import bikaMessageFactory as _
from Products.CMFCore.utils import getToolByName
from bika.lims.interfaces import IProduct
from bika.lims import config
from bika.lims.content.bikaschema import BikaSchema
from decimal import Decimal
from Products.Archetypes.public import *
from Products.Archetypes.references import HoldingReference
from bika.sanbi.browser.widgets import ProductSuppliersWidget

schema = BikaSchema.copy() + Schema((
    ReferenceField('Category',
        required=1,
        vocabulary='getCategories',
        allowed_types=('ProductCategory',),
        relationship='ProductCategory',
        referenceClass=HoldingReference,
        widget=ReferenceWidget(
            checkbox_bound=0,
            label = _("Product Category"),
            description = _(""),
        ),
    ),
    ReferenceField('Manufacturer',
        vocabulary='getManufacturers',
        allowed_types=('Manufacturer',),
        relationship='InstrumentManufacturer',
        required=1,
        widget=SelectionWidget(
           format='select',
           label=_("Manufacturer"),
           visible={'view': 'invisible', 'edit': 'visible'}
        ),
    ),

    ComputedField('SupplierUID',
        expression = 'context.aq_parent.portal_type=="Supplier" and context.aq_parent.UID() or ""',
        widget = ComputedWidget(
            visible = False,
        ),
    ),
    StringField('CAS',
        searchable = True,
        widget = StringWidget(
            label=_("CAS Registry Number"),
        ),
    ),
    StringField('SupplierCatalogueID',
        searchable = True,
        widget = StringWidget(
            label=_("Supplier Catalogue ID"),
        ),
    ),
    BooleanField('Hazardous',
        default = False,
        widget = BooleanWidget(
            label=_("Hazardous"),
            description=_("Samples of this type should be treated as hazardous"),
        ),
    ),
    IntegerField('Quantity',
        widget=IntegerWidget(
            label=_("Quantity"),
            description=_("The number of items of this product already in "
                       "storage. eg. 15, 100"),
        ),
    ),
    StringField('Unit',
        widget=StringWidget(
            label=_("Unit"),
            description=_(" Unit for the quantity eg. ml or kg"),
        ),
    ),
    FileField('FirstAidSOP',
        schemata="Documents",
        widget=FileWidget (
            label = _("First Aid SOP")),
            description=_("Standard operating procedures for first aid."),
    ),
    FileField('DisposalSOP',
        schemata="Documents",
        widget=FileWidget (
            label = _("Disposal SOP")),
            description=_("Standard operating procedures for disposal of the product."),
    ),
    FileField('SpillHandlingSOP',
        schemata="Documents",
        widget=FileWidget (
            label = _("Spill-handling SOP")),
            description=_("Standard operating procedures for handling spillage of the product."),
    ),
    FileField('MaterialSafetyDataSheets',
        schemata="Documents",
        widget=FileWidget (
            label = _("Material Safety Data Sheets")),
    ),
    ComputedField('CategoryTitle',
        expression="context.getCategory() and context.getCategory().Title() or ''",
        widget=ComputedWidget(visible=False),
    ),
    FixedPointField('VAT',
        schemata='Price',
        default_method='getDefaultVAT',
        widget = DecimalWidget(
            label=_("VAT %"),
            description=_("Enter percentage value eg. 14.0"),
        ),
    ),
    FixedPointField('Price',
        schemata='Price',
        default='0.00',
        widget = DecimalWidget(
            label=_("Price excluding VAT"),
        )
    ),
    ComputedField('VATAmount',
        expression = 'context.getVATAmount()',
        widget = ComputedWidget(
            label=_("VAT"),
            visible = {'edit':'hidden', }
        ),
    ),
    ComputedField('TotalPrice',
        expression = 'context.getTotalPrice()',
        widget = ComputedWidget(
            label=_("Total price"),
            visible = {'edit':'hidden', }
        ),
    ),

    ReferenceField('Supplier',
        required=1,
        multiValued=1,
        allowed_types=('Supplier',),
        relationship='ProductSuppliers',
        widget=ProductSuppliersWidget(
           label=_("Suppliers"),
           description="",
        )),
))

schema['description'].schemata = 'default'
schema['description'].widget.visible = True

class Product(BaseContent):
    security = ClassSecurityInfo()
    implements(IProduct)
    schema = schema
    
    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def getCategories(self):
        bsc = getToolByName(self, 'bika_setup_catalog')
        deps = []
        for d in bsc(portal_type='ProductCategory',
                     inactive_state='active'):
            deps.append((d.UID, d.Title))
        return DisplayList(deps)

    def getManufacturers(self):
        bsc = getToolByName(self, 'bika_setup_catalog')
        items = [(c.UID, c.Title) \
                 for c in bsc(portal_type='Manufacturer',
                              inactive_state='active')]
        items.sort(lambda x, y: cmp(x[1], y[1]))
        return DisplayList(items)

    def getSuppliers(self):
        bsc = getToolByName(self, 'bika_setup_catalog')
        items = [(c.UID, c.getName) \
                 for c in bsc(portal_type='Supplier',
                              inactive_state='active')]
        items.sort(lambda x, y: cmp(x[1], y[1]))
        return DisplayList(items)

    def getTotalPrice(self):
        """ compute total price """
        price = self.getPrice()
        price = Decimal(price or '0.00')
        vat = Decimal(self.getVAT())
        price = price and price or 0
        vat = vat and vat / 100 or 0
        price = price + (price * vat)
        return price.quantize(Decimal('0.00'))

    def getDefaultVAT(self):
        """ return default VAT from bika_setup """
        try:
            vat = self.bika_setup.getVAT()
            return vat
        except ValueError:
            return "0.00"

    security.declarePublic('getVATAmount')
    def getVATAmount(self):
        """ Compute VATAmount
        """
        try:
            vatamount = self.getTotalPrice() - Decimal(self.getPrice())
        except:
            vatamount = Decimal('0.00')
        return vatamount.quantize(Decimal('0.00'))

    def getSupplierTitle(self):
        return self.aq_parent.Title()

registerType(Product, config.PROJECTNAME)
