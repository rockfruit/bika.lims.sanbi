# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from plone.dexterity.browser import edit
from AccessControl import Unauthorized

class EditForm(edit.DefaultEditForm):
    """
    This class is made to check the edit form permissions against client's contact users
    """
    def __call__(self):
        # Checking current user permissions
        if self.context.hasUserAddEditPermission():
            return edit.DefaultEditForm.__call__(self)
        else:
            raise Unauthorized
