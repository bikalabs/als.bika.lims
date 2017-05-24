# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
import plone
from Acquisition._Acquisition import aq_inner
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.client.workflow import ClientWorkflowAction
from bika.lims.workflow import doActionFor

class BatchWorkflowAction(ClientWorkflowAction):
    """This function is called to do the worflow actions on objects
    acted on in bika-listing views in batch context
    """

    def __call__(self):
        form = self.request.form
        plone.protect.CheckAuthenticator(form)
        self.context = aq_inner(self.context)

        # use came_from to decide which UI action was clicked.
        # "workflow_action" is the action name specified in the
        # portal_workflow transition url.
        came_from = "workflow_action"
        action = form.get(came_from, '')
        if not action and not form.get('bika_listing_filter_bar_submit', ''):
            # workflow_action_button is the action name specified in
            # the bika_listing_view table buttons.
            came_from = "workflow_action_button"
            action = form.get('workflow_action_id', '')
            if not action:
                if self.destination_url == "":
                    self.destination_url = self.request.get_header(
                        "referer", self.context.absolute_url())
                self.request.response.redirect(self.destination_url)
                return

        if action == "sample":
            self.workflow_action_sample()
        else:
            ClientWorkflowAction.__call__(self)

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
            try:
                sampler = form['getSampler'][0][obj_uid].strip()
            except KeyError:
                sampler = obj.getSampler()
            try:
                datesampled = form['getDateSampled'][0][obj_uid].strip()
            except KeyError:
                datesampled = obj.getDateSampled()
            sampler = sampler if sampler else ''
            datesampled = DateTime(datesampled) if datesampled else ''
            if not all ([sampler, datesampled]):
                continue

            # write them to the sample
            sample.setSampler(sampler)
            sample.setDateSampled(datesampled)
            sample.reindexObject()
            ars = sample.getAnalysisRequests()
            # Analyses and AnalysisRequets have calculated fields
            # that are indexed; re-index all these objects.
            for ar in ars:
                ar.reindexObject()
                analyses = sample.getAnalyses({'review_state':
                                                   'to_be_sampled'})
                for a in analyses:
                    a.getObject().reindexObject()

            # transition the object if both values are present
            if sampler and datesampled:
                doActionFor(sample, "sample")
                new_state = workflow.getInfoFor(sample, 'review_state')
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
        self.destination_url = self.request.get_header(
            "referer", self.context.absolute_url())
        self.request.response.redirect(self.destination_url)
