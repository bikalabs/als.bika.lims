# -*- coding: utf-8 -*-
#
# This file is part of Bika LIMS
#
# Copyright 2011-2017 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

import json

from zope.i18n.locales import locales
from zope.interface import implements

from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.layout.globals.interfaces import IViewView

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from bika.lims import api
from bika.lims import logger
from bika.lims.utils import t
from bika.lims.utils import dicts_to_dict
from bika.lims.utils import logged_in_client
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.bika_listing import BikaListingView
from bika.lims.browser.sample import SamplePartitionsView


class AnalysisRequestAnalysesView(BikaListingView):
    implements(IFolderContentsView, IViewView)

    template = ViewPageTemplateFile("templates/analysisrequest_analyses.pt")

    def __init__(self, context, request):
        super(AnalysisRequestAnalysesView, self).__init__(context, request)
        self.catalog = "bika_setup_catalog"
        self.contentFilter = {
            'portal_type': 'AnalysisService',
            'sort_on': 'sortable_title',
            'inactive_state': 'active',
        }
        self.context_actions = {}
        self.icon = self.portal_url + "/++resource++bika.lims.images/analysisrequest_big.png"
        self.title = self.context.Title()
        self.sort_on = 'Title'
        self.sort_order = 'ascending'
        self.show_sort_column = False
        self.show_select_row = False
        self.show_select_column = True
        self.table_only = True
        self.show_select_all_checkbox = False
        self.pagesize = 999999

        self.categories = []
        self.do_cats = self.context.bika_setup.getCategoriseAnalysisServices()
        if self.do_cats:
            self.show_categories = True
            self.expand_all_categories = False
            self.ajax_categories = True
            self.category_index = 'getCategoryTitle'

        self.columns = {
            'Title': {
                'title': _('Service'),
                'index': 'sortable_title',
                'sortable': False,
            },
            'Unit': {
                'title': _('Unit'),
                'sortable': False,
            },
            'Hidden': {
                'title': _('Hidden'),
                'sortable': False,
                'type': 'boolean',
            },
            'Price': {
                'title': _('Price'),
                'sortable': False,
            },
            'Priority': {
                'title': _('Priority'),
                'sortable': False,
                'index': 'Priority',
                'toggle': True,
            },
            'Partition': {
                'title': _('Partition'),
                'sortable': False,
            },
            'min': {
                'title': _('Min'),
            },
            'max': {
                'title': _('Max'),
            },
            'error': {
                'title': _('Permitted Error %'),
            },
        }

        columns = ['Title', 'Unit', 'Hidden', ]
        ShowPrices = self.context.bika_setup.getShowPrices()
        if ShowPrices:
            columns.append('Price')
            columns.append('Priority')
        ShowPartitions = self.context.bika_setup.getShowPartitions()
        if ShowPartitions:
            columns.append('Partition')
        EnableARSpecs = self.context.bika_setup.getEnableARSpecs()
        if EnableARSpecs:
            columns.append('min')
            columns.append('max')
            columns.append('error')

        self.review_states = [
            {
                'id': 'default',
                'title': _('All'),
                'contentFilter': {},
                'columns': columns,
                'transitions': [{'id': 'empty'}, ],  # none
                'custom_actions': [{'id': 'save_analyses_button',
                                    'title': _('Save')}, ],
            },
        ]

        # Create Partitions View for this ARs sample
        sample = self.context.getSample()
        p = SamplePartitionsView(sample, self.request)
        p.table_only = True
        p.allow_edit = False
        p.form_id = "parts"
        p.show_select_column = False
        p.show_table_footer = False
        p.review_states[0]['transitions'] = [{'id': 'empty'}, ]  # none
        p.review_states[0]['custom_actions'] = []
        p.review_states[0]['columns'] = ['PartTitle',
                                         'getContainer',
                                         'getPreservation',
                                         'state_title']

        self.parts = p.contents_table()

    def get_service_by_keyword(self, keyword, default=None):
        """Get a service by keyword
        """
        logger.info("Get service by keyword={}".format(keyword))
        bsc = api.get_tool("bika_setup_catalog")
        results = bsc(portal_type='AnalysisService',
                      getKeyword=keyword)
        if not results:
            logger.exception("No Analysis Service found for Keyword '{}'. "
                             "Related: LIMS-1614".format(keyword))
            return default
        elif len(results) > 1:
            logger.exception("More than one Analysis Service found for Keyword '{}'. "
                             .format(keyword))
            return default
        else:
            return api.get_object(results[0])

    def getResultsRange(self):
        """Return the AR Specs sorted by Service UID, so that the JS can
        work easily with the values.
        """

        rr_dict_by_service_uid = {}
        rr = self.context.getResultsRange()

        for r in rr:
            uid = r.get("uid", None)
            if not uid:
                # get the AS by keyword
                keyword = r.get("keyword")
                service = self.get_service_by_keyword(keyword, None)
                if service is not None:
                    uid = api.get_uid(service)
            if uid:
                rr_dict_by_service_uid[uid] = r

        return json.dumps(rr_dict_by_service_uid)

    def get_spec_from_ar(self, ar, keyword):
        empty = {'min': '', 'max': '', 'error': '', 'keyword': keyword}
        spec = ar.getResultsRange()
        if spec:
            return dicts_to_dict(spec, 'keyword').get(keyword, empty)
        return empty

    def isItemAllowed(self, obj):
        """
        It checks if the item can be added to the list depending on the
        department filter. If the analysis service is not assigned to a
        department, show it.
        If department filtering is disabled in bika_setup, will return True.
        """
        if not self.context.bika_setup.getAllowDepartmentFiltering():
            return True
        # Gettin the department from analysis service
        obj_dep = obj.getDepartment()
        result = True
        if obj_dep:
            # Getting the cookie value
            cookie_dep_uid = self.request.get('filter_by_department_info', 'no')
            # Comparing departments' UIDs
            result = True if obj_dep.UID() in\
                cookie_dep_uid.split(',') else False
            return result
        return result

    def folderitems(self):
        self.categories = []

        analyses = self.context.getAnalyses(full_objects=True)
        self.analyses = dict([(a.getServiceUID(), a) for a in analyses])
        self.selected = self.analyses.keys()
        self.show_categories = \
            self.context.bika_setup.getCategoriseAnalysisServices()
        self.expand_all_categories = False

        wf = getToolByName(self.context, 'portal_workflow')
        mtool = getToolByName(self.context, 'portal_membership')

        self.allow_edit = mtool.checkPermission('Modify portal content',
                                                self.context)

        items = BikaListingView.folderitems(self)
        analyses = self.context.getAnalyses(full_objects=True)

        parts = self.context.getSample().objectValues('SamplePartition')
        partitions = [{'ResultValue': o.Title(),
                       'ResultText': o.getId()}
                      for o in parts
                      if wf.getInfoFor(o, 'cancellation_state', '') == 'active']

        for item in items:
            if 'obj' not in item:
                continue
            obj = item['obj']

            cat = obj.getCategoryTitle()
            item['category'] = cat
            if cat not in self.categories:
                self.categories.append(cat)

            item['selected'] = item['uid'] in self.selected

            item['class']['Title'] = 'service_title'

            # js checks in row_data if an analysis may be removed.
            row_data = {}
            item['row_data'] = json.dumps(row_data)

            calculation = obj.getCalculation()
            item['Calculation'] = calculation and calculation.Title()

            locale = locales.getLocale('en')
            currency = self.context.bika_setup.getCurrency()
            symbol = locale.numbers.currencies[currency].symbol
            item['before']['Price'] = symbol
            item['Price'] = obj.getPrice()
            item['class']['Price'] = 'nowrap'
            item['Priority'] = ''

            if item['selected']:
                item['allow_edit'] = ['Partition', 'min', 'max', 'error']
                if not logged_in_client(self.context):
                    item['allow_edit'].append('Price')

            item['required'].append('Partition')
            item['choices']['Partition'] = partitions

            if obj.UID() in self.analyses:
                analysis = self.analyses[obj.UID()]
                part = analysis.getSamplePartition()
                part = part and part or obj
                item['Partition'] = part.Title()
                spec = self.get_spec_from_ar(self.context,
                                             analysis.getService().getKeyword())
                item["min"] = spec.get("min", '')
                item["max"] = spec.get("max", '')
                item["error"] = spec.get("error", '')
                # Add priority premium
                item['Price'] = analysis.getPrice()
                priority = analysis.getPriority()
                item['Priority'] = priority and priority.Title() or ''
            else:
                item['Partition'] = ''
                item["min"] = ''
                item["max"] = ''
                item["error"] = ''
                item["Priority"] = ''

            after_icons = ''
            if obj.getAccredited():
                after_icons += "<img\
                src='%s/++resource++bika.lims.images/accredited.png'\
                title='%s'>" % (
                    self.portal_url,
                    t(_("Accredited"))
                )
            if obj.getReportDryMatter():
                after_icons += "<img\
                src='%s/++resource++bika.lims.images/dry.png'\
                title='%s'>" % (
                    self.portal_url,
                    t(_("Can be reported as dry matter"))
                )
            if obj.getAttachmentOption() == 'r':
                after_icons += "<img\
                src='%s/++resource++bika.lims.images/attach_reqd.png'\
                title='%s'>" % (
                    self.portal_url,
                    t(_("Attachment required"))
                )
            if obj.getAttachmentOption() == 'n':
                after_icons += "<img\
                src='%s/++resource++bika.lims.images/attach_no.png'\
                title='%s'>" % (
                    self.portal_url,
                    t(_('Attachment not permitted'))
                )
            if after_icons:
                item['after']['Title'] = after_icons

            # Display analyses for this Analysis Service in results?
            ser = self.context.getAnalysisServiceSettings(obj.UID())
            item['allow_edit'] = ['Hidden', ]
            item['Hidden'] = ser.get('hidden', obj.getHidden())
            item['Unit'] = obj.getUnit()

        self.categories.sort()
        return items
