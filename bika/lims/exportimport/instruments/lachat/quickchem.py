# -*- coding: utf-8 -*-
""" Lachat QuickChem FIA
"""
import re
import csv
import json
import logging
import traceback

from bika.lims import bikaMessageFactory as _
from bika.lims.exportimport.instruments.resultsimport import \
    AnalysisResultsImporter, InstrumentResultsFileParser
from bika.lims.utils import t

logger = logging.getLogger(__name__)

title = "Lachat QuickChem FIA"


class Parser(InstrumentResultsFileParser):
    """ Instrument Parser
    """

    def __init__(self, rsf):
        InstrumentResultsFileParser.__init__(self, rsf, 'CSV')

    def parse(self):
        """ CSV Parser
        """

        reader = csv.DictReader(self.getInputFile(), delimiter='\t')

        for row in reader:
            # in Sample ID column, we may find format: '[SampleID] samplepoint'
            sampleid = row['Sample ID']
            if sampleid.startswith('['):
                # the part between brackets is the sample id:
                row['Sample ID'] = sampleid[1:].split(']')[0]

            # Strip all special chars from the service name (Analyte Name col)
            row['Analyte Name'] = re.sub(r"\W", "", row['Analyte Name'])

            row['DefaultResult'] = 'Peak Concentration'
            self._addRawResult(row['Sample ID'],
                               values={row['Analyte Name']: row},
                               override=False)

        self.log(
            "End of file reached successfully: ${total_objects} objects, "
            "${total_analyses} analyses, ${total_results} results",
            mapping={"total_objects": self.getObjectsTotalCount(),
                     "total_analyses": self.getAnalysesTotalCount(),
                     "total_results": self.getResultsTotalCount()}
        )

        return True


class Importer(AnalysisResultsImporter):
    """ Instrument Importer
    """

    def __init__(self, parser, context, idsearchcriteria, override,
                 allowed_ar_states=None, allowed_analysis_states=None,
                 instrument_uid=None):
        AnalysisResultsImporter.__init__(self,
                                         parser,
                                         context,
                                         idsearchcriteria,
                                         override,
                                         allowed_ar_states,
                                         allowed_analysis_states,
                                         instrument_uid)


def Import(context, request):
    """ Import Form
    """
    infile = request.form['lachat_quickchem_fia_file']
    fileformat = request.form['lachat_quickchem_fia_format']
    artoapply = request.form['lachat_quickchem_fia_artoapply']
    override = request.form['lachat_quickchem_fia_override']
    sample = request.form.get('lachat_quickchem_fia_sample', 'requestid')
    instrument = request.form.get('lachat_quickchem_fia_instrument', None)
    errors = []
    logs = []
    warns = []

    # Load the most suitable parser according to file extension/options/etc...
    parser = None
    if not hasattr(infile, 'filename'):
        errors.append(_("No file selected"))
    if fileformat == 'csv':
        parser = Parser(infile)
    else:
        errors.append(t(_("Unrecognized file format ${fileformat}",
                          mapping={"fileformat": fileformat})))

    if parser:
        # Load the importer
        status = ['sample_received', 'attachment_due', 'to_be_verified']
        if artoapply == 'received':
            status = ['sample_received']
        elif artoapply == 'received_tobeverified':
            status = ['sample_received', 'attachment_due', 'to_be_verified']

        over = [False, False]
        if override == 'nooverride':
            over = [False, False]
        elif override == 'override':
            over = [True, False]
        elif override == 'overrideempty':
            over = [True, True]

        sam = ['getRequestID', 'getSampleID', 'getClientSampleID']
        if sample == 'requestid':
            sam = ['getRequestID']
        if sample == 'sampleid':
            sam = ['getSampleID']
        elif sample == 'clientsid':
            sam = ['getClientSampleID']
        elif sample == 'sample_clientsid':
            sam = ['getSampleID', 'getClientSampleID']

        importer = Importer(parser=parser,
                            context=context,
                            idsearchcriteria=sam,
                            allowed_ar_states=status,
                            allowed_analysis_states=None,
                            override=over,
                            instrument_uid=instrument)
        tbex = ''
        try:
            importer.process()
        except:
            tbex = traceback.format_exc()
        errors = importer.errors
        logs = importer.logs
        warns = importer.warns
        if tbex:
            errors.append(tbex)

    results = {'errors': errors, 'log': logs, 'warns': warns}

    return json.dumps(results)
