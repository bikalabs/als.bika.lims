# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.content import schemata
from Products.Archetypes import atapi
from Products.Archetypes.ArchetypeTool import registerType
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from bika.lims.browser import BrowserView
from bika.lims.browser.bika_listing import BikaListingView
from bika.lims.config import PROJECTNAME
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from plone.app.layout.globals.interfaces import IViewView
from bika.lims.content.bikaschema import BikaFolderSchema
from plone.app.content.browser.interfaces import IFolderContentsView
from plone.app.folder.folder import ATFolder, ATFolderSchema
from bika.lims.interfaces import ISuppliers
from zope.interface.declarations import implements

class SuppliersView(BikaListingView):
    implements(IFolderContentsView, IViewView)
    def __init__(self, context, request):
        super(SuppliersView, self).__init__(context, request)
        self.catalog = 'bika_setup_catalog'
        self.contentFilter = {'portal_type': 'Supplier', 
                              'sort_on': 'sortable_title'}
        self.context_actions = {_('Add'):
                                {'url': 'createObject?type_name=Supplier',
                                 'icon': '++resource++bika.lims.images/add.png'}}
        self.title = self.context.translate(_("Suppliers"))
        self.icon = "++resource++bika.lims.images/supplier_big.png"
        self.description = ""
        self.show_sort_column = False
        self.show_select_row = False
        self.show_select_column = True
        self.sort_on = 'getName'
        self.sort_order = 'ascending'
        self.pagesize = 25

        self.columns = {
            'getName': {'title': _('getName'),
                        'index': 'getName'},
            'Email': {'title': _('Email'),
                      'toggle': True},
            'Phone': {'title': _('Phone'),
                      'toggle': True},
            'Fax': {'title': _('Fax'),
                    'toggle': True},
        }
        self.review_states = [
            {'id':'default',
             'title': _('Active'),
             'contentFilter': {'inactive_state': 'active'},
             'transitions': [{'id':'deactivate'}, ],
             'columns': ['getName', 'Email', 'Phone', 'Fax']},
            {'id':'inactive',
             'title': _('Dormant'),
             'contentFilter': {'inactive_state': 'inactive'},
             'transitions': [{'id':'activate'}, ],
             'columns': ['getName', 'Email', 'Phone', 'Fax']},
            {'id':'all',
             'title': _('All'),
             'contentFilter':{},
             'columns': ['getName', 'Email', 'Phone', 'Fax']},
        ]

    def folderitems(self):
        items = BikaListingView.folderitems(self)
        for x in range(len(items)):
            if not items[x].has_key('obj'): continue
            obj = items[x]['obj']
            items[x]['getName'] = obj.getName()
            items[x]['Email'] = obj.getEmailAddress()
            items[x]['Phone'] = obj.getPhone()
            items[x]['Fax'] = obj.getFax()
            items[x]['replace']['getName'] = "<a href='%s'>%s</a>" % \
                 (items[x]['url'], items[x]['getName'])

        return items

schema = ATFolderSchema.copy()
class Suppliers(ATFolder):
    implements(ISuppliers)
    displayContentsTab = False
    schema = schema

schemata.finalizeATCTSchema(schema, folderish = True, moveDiscussion = False)
atapi.registerType(Suppliers, PROJECTNAME)
