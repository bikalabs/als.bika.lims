# -*- coding: utf-8 -*-
#
# This file is part of Bika LIMS
#
# Copyright 2011-2017 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from bika.lims.browser.batchfolder import BatchFolderContentsView
from Products.CMFCore.utils import getToolByName


class ClientBatchesView(BatchFolderContentsView):
    def __init__(self, context, request):
        super(ClientBatchesView, self).__init__(context, request)
        self.view_url = self.context.absolute_url() + "/batches"

    def __call__(self):
        self.contentFilter['getClientTitle'] = self.context.Title()
        return BatchFolderContentsView.__call__(self)
