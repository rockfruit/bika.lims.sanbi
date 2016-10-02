import string

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims.browser.storage import getStorageTypes
from plone import api
from plone.app.layout.viewlets import ViewletBase
from zExceptions import BadRequest
from zope.dottedname.resolve import resolve
from zope.interface import alsoProvides
from zope.schema import ValidationError


class AddStorageViewlet(ViewletBase):
    index = ViewPageTemplateFile("addstorage_viewlet.pt")
    add_managed_pt = ViewPageTemplateFile("add_managed.pt")
    add_unmanaged_pt = ViewPageTemplateFile("add_unmanaged.pt")
    add_units_pt = ViewPageTemplateFile("add_units.pt")

    def storage_types(self):
        """Return UI-friendly formatted version of getStorageTypes() output
        """
        return getStorageTypes()

    def dlclass(self):
        """We want to automatically flag the viewlet expanded if there
        are no storage objects at this location.
        """
        if self.context.objectValues():
            return "collapsible collapsedOnLoad"
        else:
            return "collapsible"

    def render(self):
        return self.index()

    def addstorage_viewlet_body(self):
        return self.viewlet_body_pt()

    def add_units(self):
        return self.add_units_pt()

    def add_managed(self):
        return self.add_managed_pt(storage_types=self.storage_types())

    def add_unmanaged(self):
        return self.add_unmanaged_pt(storage_types=self.storage_types())

    def show_managed(self):
        if self.request.URL.endswith('/storage') \
                or self.request.URL.endswith('/storage/view'):
            return False
        return True

    def show_unmanaged(self):
        if self.request.URL.endswith('/storage') \
                or self.request.URL.endswith('/storage/view'):
            return False
        return True

class AddStorageSubmit(BrowserView):
    """
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):

        form = self.request.form

        if 'addstorage_managed_submitted' in form:
            return AddManagedStorage(self.context, self.request)()
        elif 'addstorage_unmanaged_submitted' in form:
            return AddUnmanagedStorage(self.context, self.request)()
        elif 'add_units_submitted' in form:
            return AddStorageUnits(self.context, self.request)()


class Storage(BrowserView):
    def __init__(self, context, request):
        super(Storage, self).__init__(context, request)
        self.context = context
        self.request = request

    def get_sequence(self, start, nr_items):
        form = self.request.form

        # Always nr_items must be int > 0.
        try:
            nr_items = int(nr_items)
        except ValueError:
            nr_items = 1
        sequence = []

        # plain numbers:
        try:
            start = int(start)
            sequence = range(start, start + nr_items)
        except ValueError:
            # Alphanumeric:
            self.validate_sequence_format(start)
            sequence = [start]
            next = start
            for x in range(nr_items - 1):  # -1 because [start] is added above
                next = self.inc_str(next)
                sequence.append(next)
        return sequence

    def validate_sequence_format(self, start):
        """Verify some format restrictions
        """
        upper_ords = [ord(x) for x in string.uppercase]
        lower_ords = [ord(x) for x in string.lowercase]
        # start format return value string of "U" and 'l" characters.
        startfmt = ""
        for char in str(start):
            o = ord(char)
            if o in upper_ords:
                startfmt += "U"
            elif o in lower_ords:
                startfmt += "l"
            else:
                msg = u"Sequence Start can be a number or letter(s), " \
                      u"but can't contain both."
                self.form_error(msg)
                raise ValidationError(msg)
        if 'l' in startfmt and 'U' in startfmt:
            self.form_error(
                "Can't have both upper and lowercase letters in one sequence.")
            raise ValidationError

    def inc_str(self, str):
        ords = [ord(x) for x in str]
        inced_ords = self.inc_ords(ords)
        return ''.join([chr(x) for x in inced_ords])

    def inc_ords(self, ords):
        """Incrememt ords in a list of ords, so that:
        - a (97) becomes b (98).
        - AZ (65, 90) becomes BA (66, 65)
        """
        out_ords = []
        inc = True  # on first pass, inc is true (always inc the rightmost ord)
        for i in range(len(ords) - 1, -1, -1):
            o = ords[i]
            if inc:
                inc = False
                o += 1
                if o == 123:
                    inc = True
                    o = 97
                if o == 91:
                    inc = True
                    o = 65
            out_ords.append(o)

        if inc == True:
            chars = ''.join([chr(x) for x in out_ords])
            msg = u"Format too short for item count starting with %s" % chars
            self.form_error(msg)
            raise ValidationError(msg)

        return reversed(out_ords)

    def storage_types(self):
        """Return UI-friendly formatted version of getStorageTypes() output
        """
        return getStorageTypes()

    def form_error(self, msg):
        self.context.plone_utils.addPortalMessage(msg)
        self.request.response.redirect(self.context.absolute_url())


class AddStorageUnits(Storage):
    def __init__(self, context, request):
        super(AddStorageUnits, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):

        try:
            self.validate_form_inputs()
        except ValidationError:
            return

        units = self.create_units()

        msg = u'%s Storage units created.' % len(units)
        self.context.plone_utils.addPortalMessage(msg)
        self.request.response.redirect(self.context.absolute_url())

    def create_units(self):
        """Create the new storage unit items from form values.
        """
        form = self.request.form
        # titles
        titletemplate = form.get('units_titletemplate', None)
        idtemplate = form.get('units_idtemplate', None)
        # schema
        unittype = form.get('units_type_uid', None)
        temperature = form.get('units_temperature', '')
        department = form.get('units_department_uid', None)
        address = form.get('units_address', None)  # schema

        start = form['units_start']
        nr_items = int(form['units_nr_items'])

        units = []
        for x in self.get_sequence(start, nr_items):
            try:
                instance = api.content.create(
                    container=self.context,
                    type="StorageUnit",
                    id=idtemplate.format(id=x),
                    title=titletemplate.format(id=x))
            except BadRequest as e:
                msg = e.message
                self.form_error(msg)
                self.request.response.redirect(self.context.absolute_url())
                return []

            # schema
            self.set_inputs_into_schema(
                instance,
                temperature,
                department,
                address,
                unittype
            )
            self.context.manage_renameObject(
                instance.id, idtemplate.format(id=x))
            units.append(instance)
        return units

    def validate_form_inputs(self):
        form = self.request.form
        # Title and ID Templates
        titletemplate = self.request.form.get('units_titletemplate', None)
        idtemplate = self.request.form.get('units_idtemplate', None)
        if not (titletemplate and idtemplate):
            msg = u'ID and Title template are both required.'
            self.form_error(msg)
            raise ValidationError(msg)
        if not ('{id}' in titletemplate and '{id}' in idtemplate):
            msg = u'ID and Title templates must contain {id} for ID sequence ' \
                  u'substitution'
            self.form_error(msg)
            raise ValidationError(msg)

        # check for valid integer values
        try:
            nr_items = int(form['units_nr_items'])
        except:
            msg = u'Item count must be an integer.'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)
        if nr_items < 1:
            msg = u'Item count must be > 0.'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)

        # Check that none of the IDs conflict with existing items
        start = form['units_start']
        nr_items = int(form['units_nr_items'])
        ids = [x.id for x in self.context.objectValues()]
        for x in self.get_sequence(start, nr_items):
            if x in ids:
                msg = u'The ID %s already exists.' % x
                self.form_error(msg)
                self.request.response.redirect(self.context.absolute_url())
                raise ValidationError(msg)

    def set_inputs_into_schema(
            self, instance, temperature, department, address, unittype):
        # Set field values across each object if possible
        schema = instance.Schema()
        if temperature and 'Temperature' in schema:
            instance.Schema()['Temperature'].set(instance, temperature)
        if department and 'Department' in schema:
            instance.Schema()['Department'].set(instance, department)
        if address and 'Address' in schema:
            instance.Schema()['Address'].set(instance, address)
        if unittype and 'UnitType' in schema:
            instance.Schema()['UnitType'].set(instance, unittype)


class AddManagedStorage(Storage):
    def __init__(self, context, request):
        super(AddManagedStorage, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):

        try:
            self.validate_form_inputs()
        except ValidationError:
            return

        form = self.request.form
        storages = self.create_managed_storages()

        msg = u'%s Managed storages created (%s to %s)' % \
              (len(storages), storages[0].id, storages[-1].id)
        self.context.plone_utils.addPortalMessage(msg)
        self.request.response.redirect(self.context.absolute_url())

    def create_managed_storages(self):
        """Create the new managed storages from form values.
        """
        form = self.request.form
        # titles
        titletemplate = form.get('managed_titletemplate', None)
        idtemplate = form.get('managed_idtemplate', None)
        # schema
        temperature = form.get('managed_temperature', '')
        department = form.get('managed_department', None)
        address = form.get('managed_address', None)

        start = form['managed_start']
        nr_items = int(form['managed_nr_items'])

        nr_positions = int(form.get('managed_positions', 0))

        storage_types = form.get('managed_storage_types', [])
        if isinstance(storage_types, basestring):
            storage_types = [storage_types]

        XAxis = form.get('managed_x', nr_positions)
        YAxis = form.get('managed_y', 0)

        storages = []
        for x in self.get_sequence(start, nr_items):
            storage = api.content.create(
                container=self.context,
                type="ManagedStorage",
                id=idtemplate.format(id=x),
                title=titletemplate.format(id=x),
                XAxis=int(XAxis),
                YAxis=int(YAxis)
            )
            # schema
            self.set_inputs_into_schema(
                storage, temperature, department, address)
            # storage types are set on this managed storage:
            self.set_storage_types(storage, storage_types)
            storage.reindexObject()
            # Create storage positions
            for p in range(1, nr_positions + 1):
                pos = api.content.create(
                    container=storage,
                    type="StoragePosition",
                    id="{id}".format(id=p),  # XXX hardcoded pos title and id
                    title="{id}".format(id=p))
                # storage types are set on each pos inside the storage too.
                self.set_storage_types(pos, storage_types)

            storages.append(storage)

        return storages

    def set_storage_types(self, instance, storage_types):
        # Set field values across each object if possible
        schema = instance.Schema()
        if storage_types and 'StorageTypes' in schema:
            instance.Schema()['StorageTypes'].set(instance, storage_types)
        self.provide_storagetype_interfaces(instance, storage_types)

    def provide_storagetype_interfaces(self, instance, storage_types):
        """Assign any selected storage type interfaces to this location.
        """
        for storage_type in storage_types:
            inter = resolve(storage_type)
            alsoProvides(instance, inter)

    def validate_form_inputs(self):
        form = self.request.form
        # Title and ID Templates
        titletemplate = form.get('managed_titletemplate', None)
        idtemplate = form.get('managed_idtemplate', None)
        if not (titletemplate and idtemplate):
            msg = u'ID and Title template are both required.'
            self.form_error(msg)
            raise ValidationError(msg)
        if not ('{id}' in titletemplate and '{id}' in idtemplate):
            msg = u'ID and Title templates must contain {id} for ID sequence ' \
                  u'substitution'
            self.form_error(msg)
            raise ValidationError(msg)

        # check for valid integer values
        try:
            nr_items = int(form.get('managed_nr_items', None))
            nr_positions = int(form.get('managed_positions', 0))
            fnrp = form.get('managed_positions', 0)
            if not fnrp:
                fnrp = 0
            nr_positions = int(fnrp)
        except:
            msg = u'Item and position count must be numbers'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)
        if nr_items < 1:
            msg = u'Item count must be > 0.'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)
        if nr_positions < 1:
            msg = u'Position count must be > 1.'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)

        # verify storage_type interface selection
        storage_types = form.get('managed_storage_types', [])
        if any([storage_types, nr_positions]) \
                and not all([storage_types, nr_positions]):
            raise ValidationError(
                u'To create managed storage, at least one storage type must be '
                u'selected, and the number of storage positions must be > 0.')

        # Verify
        Dimension = form.get('managed_dimension', 'First')
        XAxis = form.get('managed_x', nr_positions)
        YAxis = form.get('managed_y', 0)
        ZAxis = form.get('managed_z', 0)

        # Check that none of the IDs conflict with existing items
        start = form['managed_start']
        nr_items = int(form['managed_nr_items'])
        ids = [x.id for x in self.context.objectValues()]
        for x in self.get_sequence(start, nr_items):
            if x in ids:
                msg = u'The ID %s already exists.' % x
                self.form_error(msg)
                self.request.response.redirect(self.context.absolute_url())
                raise ValidationError(msg)

    def set_inputs_into_schema(
            self, instance, temperature, department, address):
        # Set field values across each object if possible
        schema = instance.Schema()
        if temperature and 'Temperature' in schema:
            instance.Schema()['Temperature'].set(instance, temperature)
        if department and 'Department' in schema:
            instance.Schema()['Department'].set(instance, temperature)
        if address and 'Address' in schema:
            instance.Schema()['Address'].set(instance, temperature)

    def form_error(self, msg):
        self.context.plone_utils.addPortalMessage(msg)
        self.request.response.redirect(self.context.absolute_url())


class AddUnmanagedStorage(Storage):
    def __init__(self, context, request):
        super(AddUnmanagedStorage, self).__init__(context, request)
        self.context = context
        self.request = request

    def __call__(self):

        try:
            self.validate_form_inputs()
        except ValidationError:
            return

        form = self.request.form
        storages = self.create_unmanaged_storages()

        msg = u'%s Unmanaged storages created (%s to %s)' % \
              (len(storages), storages[0].id, storages[-1].id)
        self.context.plone_utils.addPortalMessage(msg)
        self.request.response.redirect(self.context.absolute_url())

    def provide_storagetype_interfaces(self, instance, storage_types):
        """Assign any selected storage type interfaces to this location.
        """
        for storage_type in storage_types:
            inter = resolve(storage_type)
            alsoProvides(instance, inter)

    def create_unmanaged_storages(self):
        """Create the new unmanaged storages from form values.
        """
        form = self.request.form
        # titles
        titletemplate = form.get('unmanaged_titletemplate', None)
        idtemplate = form.get('unmanaged_idtemplate', None)
        # schema
        temperature = form.get('unmanaged_temperature', '')
        department = form.get('unmanaged_department', None)
        address = form.get('unmanaged_address', None)

        start = form['unmanaged_start']
        nr_items = int(form['unmanaged_nr_items'])

        storage_types = form.get('unmanaged_storage_types', [])
        if isinstance(storage_types, basestring):
            storage_types = [storage_types]

        storages = []
        for x in self.get_sequence(start, nr_items):
            instance = api.content.create(
                container=self.context,
                type="UnmanagedStorage",
                id=idtemplate.format(id=x),
                title=titletemplate.format(id=x))
            # schema
            self.set_inputs_into_schema(
                instance, temperature, department, address)
            if instance.id != idtemplate.format(id=x):
                self.context.manage_renameObject(
                    instance.id, idtemplate.format(id=x))
            instance.reindexObject()
            # storage types are set on this unmanaged storage:
            self.set_storage_types(instance, storage_types)
            storages.append(instance)
        return storages

    def validate_form_inputs(self):
        form = self.request.form
        # Title and ID Templates
        titletemplate = form.get('unmanaged_titletemplate', None)
        idtemplate = self.request.form.get('unmanaged_idtemplate', None)
        if not (titletemplate and idtemplate):
            self.form_error(u'ID and Title template are both required.')
            raise ValidationError
        if not ('{id}' in titletemplate and '{id}' in idtemplate):
            msg = u'ID and Title templates must contain {id} for ID sequence ' \
                  u'substitution'
            self.form_error(msg)
            raise ValidationError(msg)

        # check for valid integer values
        try:
            nr_items = int(self.request.form.get('unmanaged_nr_items', None))
        except:
            msg = u'Item count must be an integer.'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)

        if nr_items < 1:
            msg = u'Item count must be > 0'
            self.form_error(msg)
            self.request.response.redirect(self.context.absolute_url())
            raise ValidationError(msg)

        # Check that none of the IDs conflict with existing items
        start = form['unmanaged_start']
        nr_items = int(form['unmanaged_nr_items'])
        ids = [x.id for x in self.context.objectValues()]
        for x in self.get_sequence(start, nr_items):
            if x in ids:
                msg = u'The ID %s already exists.' % x
                self.form_error(msg)
                self.request.response.redirect(self.context.absolute_url())
                raise ValidationError(msg)

    def set_inputs_into_schema(
            self, instance, temperature, department, address):
        # Set field values across each object if possible
        schema = instance.Schema()
        if temperature and 'Temperature' in schema:
            instance.Schema()['Temperature'].set(instance, temperature)
        if department and 'Department' in schema:
            instance.Schema()['Department'].set(instance, temperature)
        if address and 'Address' in schema:
            instance.Schema()['Address'].set(instance, temperature)
