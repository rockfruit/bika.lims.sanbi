# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from views.batches import ClientBatchesView
from views.analysisrequests import ClientAnalysisRequestsView
from views.analysisrequests import ClientBatchAnalysisRequestsView
from views.samples import ClientSamplesView
from views.analysisprofiles import ClientAnalysisProfilesView
from views.artemplates import ClientARTemplatesView
from views.srtemplates import ClientSRTemplatesView
from views.samplepoints import ClientSamplePointsView
from views.analysisspecs import ClientAnalysisSpecsView
from views.analysisspecs import SetSpecsToLabDefaults
from views.attachments import ClientAttachmentsView
from views.orders import ClientOrdersView
from views.contacts import ClientContactsView
from views.contacts import ClientContactVocabularyFactory
from views.samplingrounds import ClientSamplingRoundsView

from ajax import ReferenceWidgetVocabulary
from ajax import ajaxGetClientInfo

from workflow import ClientWorkflowAction
