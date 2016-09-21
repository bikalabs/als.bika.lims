# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.bika_listing import WorkflowAction
from bika.lims.workflow import doActionFor

class BatchWorkflowAction(WorkflowAction):
    """This function is called to do the worflow actions on objects
    acted on in bika-listing views in batch context
    """

    def workflow_action_sample(self):
        workflow = getToolByName(self.context, 'portal_workflow')
        form = self.request.form

        objects = self._get_selected_items(self)
        transitioned = {'to_be_preserved': [], 'sample_due': []}
        for obj_uid, obj in objects.items():
            if obj.portal_type == "AnalysisRequest":
                ar = obj
                sample = obj.getSample()
            else:
                sample = obj
                ar = sample.aq_parent
            # can't transition inactive items
            if workflow.getInfoFor(sample, 'inactive_state', '') == 'inactive':
                continue

            # grab this object's Sampler and DateSampled from the form
            # (if the columns are available and edit controls exist)
            if 'getSampler' in form and 'getDateSampled' in form:
                try:
                    Sampler = form['getSampler'][0][obj_uid].strip()
                    DateSampled = form['getDateSampled'][0][obj_uid].strip()
                except KeyError:
                    continue
                Sampler = Sampler and Sampler or ''
                DateSampled = DateSampled and DateTime(DateSampled) or ''
            else:
                continue

            # write them to the sample
            sample.setSampler(Sampler)
            sample.setDateSampled(DateSampled)
            sample.reindexObject()
            ars = sample.getAnalysisRequests()
            # Analyses and AnalysisRequets have calculated fields
            # that are indexed; re-index all these objects.
            for ar in ars:
                ar.reindexObject()
                analyses = sample.getAnalyses({'review_state': 'to_be_sampled'})
                for a in analyses:
                    a.getObject().reindexObject()

            # transition the object if both values are present
            if Sampler and DateSampled:
                doActionFor(sample, "sample")
                new_state = workflow.getInfoFor(sample, 'review_state')
                doActionFor(ar, "sample")
                transitioned[new_state].append(sample.Title())

        message = None
        for state in transitioned:
            tlist = transitioned[state]
            if len(tlist) > 1:
                if state == 'to_be_preserved':
                    message = _('${items} are waiting for preservation.',
                                mapping={'items': ', '.join(tlist)})
                else:
                    message = _('${items} are waiting to be received.',
                                mapping={'items': ', '.join(tlist)})
                self.context.plone_utils.addPortalMessage(message, 'info')
            elif len(tlist) == 1:
                if state == 'to_be_preserved':
                    message = _('${item} is waiting for preservation.',
                                mapping={'item': ', '.join(tlist)})
                else:
                    message = _('${item} is waiting to be received.',
                                mapping={'item': ', '.join(tlist)})
                self.context.plone_utils.addPortalMessage(message, 'info')
        if not message:
            message = _('No changes made.')
            self.context.plone_utils.addPortalMessage(message, 'info')
        self.destination_url = self.request.get_header("referer",
                                                       self.context.absolute_url())
        self.request.response.redirect(self.destination_url)
