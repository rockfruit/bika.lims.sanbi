# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from bika.lims.controlpanel.bika_instruments import InstrumentsView

class ManufacturerInstrumentsView(InstrumentsView):

    def __init__(self, context, request):
        super(ManufacturerInstrumentsView, self).__init__(context, request)

    def folderitems(self):
        items = InstrumentsView.folderitems(self)
        uidsup = self.context.UID()
        outitems = []
        for x in range(len(items)):
            obj = items[x]['obj']
            if obj.getManufacturer().UID() == uidsup:
                outitems.append(items[x])
        return outitems
