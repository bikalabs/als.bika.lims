from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from plone.resource.utils import iterDirectoriesOfType, queryResourceDirectory
from plone.resource.utils import queryResourceDirectory

from bika.lims import bikaMessageFactory as _, t
from bika.lims import logger
from bika.lims.browser import BrowserView
from bika.lims.vocabularies import getStickerTemplates
from bika.lims.browser import BrowserView
from bika.lims.utils import createPdf

import os
import traceback


class Sticker(BrowserView):
    template = ViewPageTemplateFile("templates/stickerpdf.pt")

    def __call__(self):
        """Render PDF stickers using the template and items passed to us in the
        request.  The PDF is returned directly on the response.  The template
        will be rendered once for each item.  The sticker template can refer to
        view.current_item, to get the object for which it is currently rendered
        """
        # each individual sticker's rendered html gets appended to this list.
        self.htmls = []
        self.template_fn = self.get_template_filename()
        instances = self.get_items()
        for instance in instances:
            self.current_item = instance
            self.htmls.append(ViewPageTemplateFile(self.template_fn)(self))

        # Render the HTML which will be used to create the PDF.
        html = self.template()

        # createPdf returns PDF data, but also writes it to the provided
        # outfile, so I'm going to ignore the returned data.
        data = createPdf(html)

        setheader = self.request.RESPONSE.setHeader
        setheader('Content-Type', 'application/pdf')
        self.request.RESPONSE.write(data)

    def css(self):
        """ Looks for the CSS file from the selected template and return its
            contents. If the selected template is default.pt, looks for a
            file named default.css in the stickers path and return its contents.
            If no CSS file found, returns an empty string
        """
        css_fn = self.template_fn.replace(".pt", ".css")
        return open(css_fn).read() if os.path.exists(css_fn) else ""


    def get_template_filename(self):
        """Get the template name.  It can come from:
        - bika_setup.AutoStickerTemplate
        - request.template
        Perhaps the name specifies the package in which the sticker lives. we
        check this by splitting the template name on ':'. if no package is
        specified, we'll assume bika.lims.
        """
        # get the name of the specified template
        template = self.request.get('template')
        if not template:
            template = self.context.bika_setup.getAutoStickerTemplate()
            assert template, "Sticker template is required and was not provided"
        # check for package name
        if ':' in template:
            prefix, template = template.split(':')
        else:
            prefix, template = 'bika.lims', template
        # Check for existence
        templates_dir = queryResourceDirectory('stickers', prefix).directory
        template_fn = os.path.join(templates_dir, template)
        assert os.path.isfile(template_fn), "%s does not exist" % template_fn
        return template_fn


    def get_items(self):
        """Return a list of objects for which we will print stickers
        Items can be specified in the "items" request parameter.
        If it's empty, or not present, we will attempt to use the current
        context as the only item.
        If the context is not one of the items for which sticker printing is
        supported, we will fail with an assertion error.
        Items for which sticker printing is supported are:
        - AnalysisRequest
        - Sample
        """
        names = self.request.get('items', '')
        if names:
            brains = self.bika_catalog(id=names.split(","))
            instances = [o.getObject() for o in brains]
        else:
            instances = [self.context, ]

        items = []
        for instance in instances:
            if instance.portal_type == 'Sample':
                items.append(instance)
            elif instance.portal_type == 'AnalysisRequest':
                items.append(instance.getSample())
            else:
                raise Exception("%s is not a Sample or AnalysisRequest")

        items.sort(cmp=lambda x,y:cmp(x.id, y.id))
        return items
