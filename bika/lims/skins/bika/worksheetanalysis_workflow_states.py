# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

## Script (Python) "worksheetanalysis_workflow_states"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Get worksheet analysis workflow states
##

states_folder = context.portal_workflow.bika_worksheetanalysis_workflow.states
state_ids = ('assigned', 'unassigned',)
l = []
for state_id in state_ids:
    state = states_folder[state_id]
    l.append( {'id': state.getId(), 'title': state.title} )
return l
