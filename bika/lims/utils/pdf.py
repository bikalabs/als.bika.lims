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
from weasyprint import HTML, CSS

from bika.lims.utils import tmpID, to_utf8
from email import Encoders

def createPdf(htmlreport, outfile=None, css=None, images={}):
    """create a PDF from some HTML.
    htmlreport: rendered html
    outfile: pdf filename; if supplied, caller is responsible for creating
             and removing it.
    css: remote URL of css file to download
    images: A dictionary containing possible URLs (keys) and local filenames
            (values) with which they may to be replaced during rendering.
    # WeasyPrint will attempt to retrieve images directly from the URL
    # referenced in the HTML report, which may refer back to a single-threaded
    # (and currently occupied) zeoclient, hanging it.  All image source
    # URL's referenced in htmlreport should be local files.
    """
    # A list of files that should be removed after PDF is written
    htmlreport = to_utf8(htmlreport)
    cleanup, htmlreport = localize_images(htmlreport)
    css_def = ''
    if css:
        if css.startswith("http://") or css.startswith("https://"):
            # Download css file in temp dir
            u = urllib2.urlopen(css)
            _cssfile = tempfile.mktemp(suffix='.css')
            localFile = open(_cssfile, 'w')
            localFile.write(u.read())
            localFile.close()
            cleanup.append(_cssfile)
        else:
            _cssfile = css
        cssfile = open(_cssfile, 'r')
        css_def = cssfile.read()


    for (key, val) in images.items():
        htmlreport = htmlreport.replace(key, val)

    # render
    htmlreport = to_utf8(htmlreport)
    renderer = HTML(string=htmlreport, encoding='utf-8')
    pdf_fn = outfile if outfile else tempfile.mktemp(suffix=".pdf")
    if css:
        renderer.write_pdf(pdf_fn, stylesheets=[CSS(string=css_def)])
    else:
        renderer.write_pdf(pdf_fn)
    # return file data
    pdf_data = open(pdf_fn, "rb").read()
    if outfile is None:
        os.remove(pdf_fn)
    for fn in cleanup:
        os.remove(fn)
    return pdf_data

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
