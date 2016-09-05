*** Settings ***

Library         BuiltIn
Library         Selenium2Library  timeout=5  implicit_wait=0.2
Library         String
Resource        keywords.txt
Resource        plone/app/robotframework/selenium.robot
Library         Remote  ${PLONEURL}/RobotRemote
Variables       plone/app/testing/interfaces.py
Variables       bika/lims/tests/variables.py

Suite Setup     Start browser
Suite Teardown  Close All Browsers

Library          DebugLibrary

*** Variables ***

*** Test Cases ***


Test Lachat QuickChem FIA importer
    Enable autologin as  LabManager
    set autologin username  test_labmanager

    Configure Objects
    Import Instrument File

    # Only one AR and one result should have been imported!
    page should contain        End of file reached successfully: 20 objects, 3 analyses, 549 results
    page should contain        ST-0001-R01: ['Analysis NitrateNitrite', 'Analysis ammonia'] imported sucessfully
    page should contain        Import finished successfully: 1 ARs and 2 results updated
    # And we must verify that the result is valid
    go to    ${PLONEURL}/clients/client-1/ST-0001-R01/manage_results
    textfield value should be        css=[selector="Result_ammonia"]    1.68

*** Keywords ***

Start browser
    Open browser                        ${PLONEURL}  chrome
    Set selenium speed                  ${SELENIUM_SPEED}

Configure Objects
    # We need a category so that we can create AnalysisServices.
    ${cat_uid} =  Create Object    bika_setup/bika_analysiscategories  AnalysisCategory  c1  title=test
    # I will just test two services for a single sample.
    ${service_uid1} =  Create Object   bika_setup/bika_analysisservices  AnalysisService  s1  title=Nitrate/Nitrite  Keyword=NitrateNitrite  Category=${cat_uid}
    ${service_uid2} =  Create Object   bika_setup/bika_analysisservices  AnalysisService  s2  title=Ammonia  Keyword=ammonia  Category=${cat_uid}
    # The quickchem inserts "Unknown" into sampletype column.  So we don't
    # care about that - but still need a sampletype for the AR
    ${st_uid} =  Create Object   bika_setup/bika_sampletypes  SampleType  ST1  title=Sample Type   Prefix=ST
    # And then create a new AR with just the one AnalysisService.
    # We'll set the ClientSampleID to match the first valid result in the XLSX.
    ${ar_uid} =  Create AR  /clients/client-1  analyses=${service_uid1},${service_uid2}  SampleType=${st_uid}   ClientSampleID=A00036896008
    # The AR and Sample must be received before any results can be added to it.
    do action for  ${ar_uid}  receive


Import Instrument File
    Go to                       ${PLONEURL}
    Click Link                  Import
    Wait until page contains    Select a data interface
    Select from list            exim  Lachat QuickChem FIA
    # This instrument supports only CSV!
    Element Should Contain      lachat_quickchem_fia_format  CSV
    ${PATH_TO_TEST} =           run keyword     resource_filename
    Choose File                 lachat_quickchem_fia_file    ${PATH_TO_TEST}/files/QuickChemFIA.csv
    Click Button                Submit
    Wait until page contains    Log trace
