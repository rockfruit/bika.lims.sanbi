# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

""" RejectAnalysis """
from Products.Archetypes.public import ReferenceField, Schema, registerType
from bika.lims.content.analysis import Analysis
from bika.lims.config import PROJECTNAME
from bika.lims.content.analysis import schema as analysis_schema


schema = analysis_schema + Schema((
    # The analysis that was originally rejected
    ReferenceField('Analysis',
        allowed_types=('Analysis',),
        relationship = 'RejectAnalysisAnalysis',
    ),
))

class RejectAnalysis(Analysis):
    archetype_name = 'RejectAnalysis'

    schema = schema


registerType(RejectAnalysis, PROJECTNAME)
