# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.Archetypes.Registry import registerField
from Products.ATExtensions.ateapi import RecordField


class AddressField(RecordField):
    """ dedicated address field"""
    _properties = RecordField._properties.copy()
    _properties.update({
        'type': 'address',
        'subfields': ('address', 'city', 'zip', 'state', 'district', 'country'),
        'outerJoin': '<br />',
    })


registerField(AddressField,
              title="Address",
              description="Used for storing address information",
)

