# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from ZODB.POSException import POSKeyError
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.bika_listing import BikaListingView


class AnalysisRequestPublishedResults(BikaListingView):
    """ View of published results
        Prints the list of pdf files with each publication dates, the user
        responsible of that publication, the emails of the addressees (and/or)
        client contact names with the publication mode used (pdf, email, etc.)
    """

    # I took IViewView away, because transitions selected in the edit-bar
    # cause errors due to wrong context, when invoked from this view, and I
    # don't know why.
    # implements(IViewView)

    def __init__(self, context, request):
        BikaListingView.__init__(self, context, request)
        self.context = context
        self.request = request

        self.catalog = "bika_catalog"
        self.contentFilter = {'portal_type': 'ARReport',
                              'sort_order': 'reverse'}
        self.context_actions = {}
        self.show_select_column = True
        self.show_workflow_action_buttons = False
        self.form_id = 'published_results'
        self.icon = "{}//++resource++bika.lims.images/report_big.png".format(
            self.portal_url)
        self.title = self.context.translate(_("Published results"))
        self.columns = {
            'Date': {'title': _('Date')},
            'PublishedBy': {'title': _('Published By')},
            'Recipients': {'title': _('Recipients')},
            'Download': {'title': _('Download')},
        }
        self.review_states = [
            {'id': 'default',
             'title': 'All',
             'contentFilter': {},
             'columns': [
                 'Date',
                 'PublishedBy',
                 'Recipients',
                 'Download',
             ]
             },
        ]

    def __call__(self):
        ar = self.context
        workflow = getToolByName(ar, 'portal_workflow')
        # If is a retracted AR, show the link to child AR and show a warn msg
        if workflow.getInfoFor(ar, 'review_state') == 'invalid':
            childar = hasattr(ar, 'getChildAnalysisRequest') \
                      and ar.getChildAnalysisRequest() or None
            childid = childar and childar.getRequestID() or None
            message = _('This Analysis Request has been withdrawn and is '
                        'shown for trace-ability purposes only. Retest: '
                        '${retest_child_id}.',
                        mapping={
                            'retest_child_id': safe_unicode(childid) or ''})
            self.context.plone_utils.addPortalMessage(
                self.context.translate(message), 'warning')
        # If is an AR automatically generated due to a Retraction, show it's
        # parent AR information
        if hasattr(ar, 'getParentAnalysisRequest') \
                and ar.getParentAnalysisRequest():
            par = ar.getParentAnalysisRequest()
            message = _('This Analysis Request has been '
                        'generated automatically due to '
                        'the retraction of the Analysis '
                        'Request ${retracted_request_id}.',
                        mapping={'retracted_request_id': par.getRequestID()})
            self.context.plone_utils.addPortalMessage(
                self.context.translate(message), 'info')
        template = BikaListingView.__call__(self)
        return template

    def contentsMethod(self, contentFilter):
        """ARReport objects associated to the current Analysis request.
        If the user is not a Manager or LabManager or Client, no items are
        displayed.
        """
        allowedroles = ['Manager', 'LabManager', 'Client', 'LabClerk']
        pm = getToolByName(self.context, "portal_membership")
        member = pm.getAuthenticatedMember()
        roles = member.getRoles()
        allowed = [a for a in allowedroles if a in roles]
        return self.context.objectValues('ARReport') if allowed else []

    def folderitem(self, obj, item, index):

        item['PublishedBy'] = self.user_fullname(obj.Creator())

        # Formatted creation date of report
        creation_date = obj.created()
        fmt_date = self.ulocalized_time(creation_date, long_format=1)
        item['Date'] = fmt_date

        # Recipients as mailto: links
        recipients = obj.getRecipients()
        links = ["<a href='mailto:{EmailAddress}'>{Fullname}</a>".format(**r)
                 for r in recipients if r['EmailAddress']]
        item['replace']['Recipients'] = ', '.join(links)

        # download link 'Download PDF (size)'
        dll = []
        try:  #
            pdf_data = obj.getPdf()
            assert pdf_data
            z = pdf_data.get_size()
            z = z / 1024 if z > 0 else 0
            dll.append("<a href='{}/at_download/Pdf'>{}</a>".format(
                obj.absolute_url(), _("Download PDF"), z))
        except (POSKeyError, AssertionError):
            # POSKeyError: 'No blob file'
            pass
        # download link 'Download CSV (size)'
        try:
            csv_data = obj.getCSV()
            assert csv_data
            z = csv_data.get_size()
            z = z / 1024 if z > 0 else 0
            dll.append("<a href='{}/at_download/CSV'>{}</a>".format(
                obj.absolute_url(), _("Download CSV"), z))
        except (POSKeyError, AssertionError):
            # POSKeyError: 'No blob file'
            pass
        item['Download'] = ''
        item['after']['Download'] = ', '.join(dll)

        return item
