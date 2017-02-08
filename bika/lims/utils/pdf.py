# -*- coding: utf-8 -*-
# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
import os
import tempfile
import urllib2
from email.mime.base import MIMEBase

import re
from pkg_resources import resource_filename
from zope.component.hooks import getSite

from bika.lims.utils import tmpID
from email import Encoders

import pdfkit

def createPdf(input, output_path, **kwargs):
    """Create a PDF from some HTML.  The arguments are passed directly to the
    pdfkit.api.from_string function, and the return value of from_string is
    returned without modification.

    The following paragraph contains the from_string arguments for reference:

    :param input: string with a desired text. Could be a raw text or a html file
    :param output_path: path to output PDF file. False means file will be returned as string.
    :param options: (optional) dict with wkhtmltopdf options, with or w/o '--'
    :param toc: (optional) dict with toc-specific wkhtmltopdf options, with or w/o '--'
    :param cover: (optional) string with url/filename with a cover html page
    :param css: (optional) string with path to css file which will be added to a input string
    :param configuration: (optional) instance of pdfkit.configuration.Configuration()
    :param configuration_first: (optional) if True, cover always precedes TOC

    Returns: True on success

    The only difference is that this function localizes all traversable images
    to filesystem paths before generating the PDF data, and deletes these
    temporary files afterwards.

    Any images or external resources that are referenced in the input, but are
    not resolvable from the portal root via traversal, must first be replaced
    with local filesystem paths before calling this fuction, for example:

        from pkg_resources import resource_filename
        path = resource_filename('bika.lims', 'skins/bika/logo_print.png')
        input = re.sub(r'''http.*logo_print[^'"]+''', "file://" + path,  input)
        pdf_data = createPdf(input, False)
    """
    temp_files, input = localize_images(input)
    retval = pdfkit.from_string(input, output_path, **kwargs)
    # remove temporary files
    for fn in temp_files:
        os.remove(fn)
    return retval

def attachPdf(mimemultipart, pdfdata, filename=None):
    """Attach a PDF file to a mime multipart message
    """
    part = MIMEBase('application', "pdf")
    fn = filename if filename else tmpID()
    part.add_header(
        'Content-Disposition', 'attachment; filename="{}.pdf"'.format(fn))
    part.set_payload(pdfdata)
    Encoders.encode_base64(part)
    mimemultipart.attach(part)

def localize_images(html):
    """The PDF renderer will attempt to retrieve attachments directly from the
    URL referenced in the HTML report, which may refer back to a single-threaded
    (and currently occupied) zeoclient, hanging it.  All images hosted via
    URLs that refer to the Plone site, must be converted to local file paths.

    This function only replaces images that can be resolved using traversal
    from the root of the Plone site.  Other images should be handled
    manually by the calling code, for example:

        path = resource_filename('bika.lims', 'skins/bika/logo_print.png')
        html = re.sub(r'''http.*logo_print[^'"]+''', "file://" + path, html)

    Returns a list of files which were created, and a modified copy
    of html where all remote URL's have been replaced with file:///...
    """
    cleanup = []
    _html = html.decode('utf-8')

    # get site URL for traversal
    portal = getSite()
    portal_url = portal.absolute_url().split("?")[0]

    # All other images should be traversable.
    for match in re.finditer("""src.*\=.*(http[^'"]*)""", _html, re.I):
        url = match.group(1)
        att_path = url.replace(portal_url+"/", "").encode('utf-8')
        attachment = portal.unrestrictedTraverse(att_path)
        if hasattr(attachment, 'getAttachmentFile'):
            attachment = attachment.getAttachmentFile()
        filename = attachment.filename
        extension = "."+filename.split(".")[-1]
        outfile, outfilename = tempfile.mkstemp(suffix=extension)
        outfile = open(outfilename, 'wb')
        outfile.write(str(attachment.data))
        outfile.close()
        _html = _html.replace(url, "file://" + outfilename)
        cleanup.append(outfilename)
    return cleanup, _html
