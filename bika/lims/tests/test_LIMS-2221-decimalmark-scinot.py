# -*- coding: utf-8 -*-

# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.
import transaction
from DateTime import DateTime
from Products.CMFPlone.FactoryTool import _createObjectByType

from bika.lims.api import get_bika_setup
from bika.lims.api import get_portal
from bika.lims.content.analysis import Analysis
from bika.lims.testing import BIKA_FUNCTIONAL_TESTING
from bika.lims.tests.base import BikaFunctionalTestCase, BikaSimpleTestCase
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.workflow import doActionFor
from plone.app.testing import login, logout
from plone.app.testing import TEST_USER_NAME
from Products.CMFCore.utils import getToolByName
import unittest

try:
    import unittest2 as unittest
except ImportError: # Python 2.7
    import unittest


class Test_DecimalMarkWithSciNotation(BikaSimpleTestCase):

    def addthing(self, folder, portal_type, **kwargs):
        thing = _createObjectByType(portal_type, folder, 'tmp')
        thing.unmarkCreationFlag()
        thing.edit(**kwargs)
        thing._renameAfterCreation()
        return thing

    def setUp(self):
        super(Test_DecimalMarkWithSciNotation, self).setUp()
        portal = get_portal()
        bika_setup = get_bika_setup()
        login(self.portal, TEST_USER_NAME)
        self.client = self.addthing(
            portal.clients, 'Client', title='Happy Hills', ClientID='HH')
        self.contact = self.addthing(
            self.client, 'Contact', Firstname='Rita', Lastname='Mohale')
        self.sampletype = self.addthing(
            bika_setup.bika_sampletypes,
            'SampleType', title='Water', Prefix='H2O')
        self.service = self.addthing(
            bika_setup.bika_analysisservices, 'AnalysisService',
            title='Calcium', Keyword='Ca')
        transaction.commit()

    def tearDown(self):
        super(Test_DecimalMarkWithSciNotation, self).setUp()
        login(self.portal, TEST_USER_NAME)

    def test_DecimalMarkWithSciNotation(self):
        # Notations
        # '1' => aE+b / aE-b
        # '2' => ax10^b / ax10^-b
        # '3' => ax10^b / ax10^-b (with superscript)
        # '4' => a·10^b / a·10^-b
        # '5' => a·10^b / a·10^-b (with superscript)
        matrix = [
            # as_prec  as_exp  not  decimalmark result    formatted result
            # -------  ------  ---  ----------- --------  --------------------
            [0,        0,      1, '0',            '0'],
            [0,        0,      2, '0',            '0'],
            [0,        0,      3, '0',            '0'],
            [0,        0,      4, '0',            '0'],
            [0,        0,      5, '0',            '0'],
            [2,        5,      1, '0.01',         '0,01'],
            [2,        5,      2, '0.01',         '0,01'],
            [2,        5,      3, '0.01',         '0,01'],
            [2,        5,      4, '0.01',         '0,01'],
            [2,        5,      5, '0.01',         '0,01'],
            [2,        1,      1, '0.123',        '1,2e-01'],
            [2,        1,      2, '0.123',        '1,2x10^-1'],
            [2,        1,      3, '0.123',        '1,2x10<sup>-1</sup>'],
            [2,        1,      4, '0.123',        '1,2·10^-1'],
            [2,        1,      5, '0.123',        '1,2·10<sup>-1</sup>'],
            [2,        1,      1, '1.234',        '1,23'],
            [2,        1,      2, '1.234',        '1,23'],
            [2,        1,      3, '1.234',        '1,23'],
            [2,        1,      4, '1.234',        '1,23'],
            [2,        1,      5, '1.234',        '1,23'],
            [2,        1,      1, '12.345',       '1,235e01'],
            [2,        1,      2, '12.345',       '1,235x10^1'],
            [2,        1,      3, '12.345',       '1,235x10<sup>1</sup>'],
            [2,        1,      4, '12.345',       '1,235·10^1'],
            [2,        1,      5, '12.345',       '1,235·10<sup>1</sup>'],
            [4,        3,      1, '-123.45678',    '-123,4568'],
            [4,        3,      2, '-123.45678',    '-123,4568'],
            [4,        3,      3, '-123.45678',    '-123,4568'],
            [4,        3,      4, '-123.45678',    '-123,4568'],
            [4,        3,      5, '-123.45678',    '-123,4568'],
            [4,        3,      1, '-1234.5678',    '-1,2345678e03'],
            [4,        3,      2, '-1234.5678',    '-1,2345678x10^3'],
            [4,        3,      3, '-1234.5678',    '-1,2345678x10<sup>3</sup>'],
            [4,        3,      4, '-1234.5678',    '-1,2345678·10^3'],
            [4,        3,      5, '-1234.5678',    '-1,2345678·10<sup>3</sup>'],
        ]
        serv = self.service
        serv.setLowerDetectionLimit('-99999') # We want to test results below 0 too
        prevm = []
        an = None
        bs = get_bika_setup()
        bs.setResultsDecimalMark(',')
        for m in matrix:
            # Create the AR and set the values to the AS, but only if necessary
            if not an or prevm[0] != m[0] or prevm[1] != m[1]:
                serv.setPrecision(m[0])
                serv.setExponentialFormatPrecision(m[1])
                self.assertEqual(serv.getPrecision(), m[0])
                self.assertEqual(serv.Schema().getField('Precision').get(serv), m[0])
                self.assertEqual(serv.getExponentialFormatPrecision(), m[1])
                self.assertEqual(serv.Schema().getField('ExponentialFormatPrecision').get(serv), m[1])
                client = self.portal.clients['client-1']
                sampletype = bs.bika_sampletypes['sampletype-1']
                values = {'Client': client.UID(),
                          'Contact': client.getContacts()[0].UID(),
                          'SamplingDate': '2015-01-01',
                          'SampleType': sampletype.UID()}
                ar = create_analysisrequest(client, {}, values, [serv.UID()])
                wf = getToolByName(ar, 'portal_workflow')
                wf.doActionFor(ar, 'receive')
                an = ar.getAnalyses()[0].getObject()
                prevm = m
            an.setResult(m[3])

            self.assertEqual(an.getResult(), m[3])
            self.assertEqual(an.Schema().getField('Result').get(an), m[3])
            fr = an.getFormattedResult(
                sciformat=m[2], decimalmark=bs.getResultsDecimalMark())
            #print '%s   %s   %s   %s  =>  \'%s\' ?= \'%s\'' % (m[0],m[1],m[2],m[3],m[4],fr)
            self.assertEqual(fr, m[4])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test_DecimalMarkWithSciNotation))
    suite.layer = BIKA_FUNCTIONAL_TESTING
    return suite
