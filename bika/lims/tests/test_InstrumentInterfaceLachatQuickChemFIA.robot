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

Test Lachat QuickChem FIA Exporter
    Enable autologin as  LabManager
    set autologin username  test_labmanager
    # Requirements for creating services and ARs:
    ${cat_uid} =  Create Object  bika_setup/bika_analysiscategories  AnalysisCategory  c1  title=test
    ${st_uid} =  Create Object   bika_setup/bika_sampletypes  SampleType  ST1  title=Sample Type   Prefix=ST
    # I will just test two services for a single sample.
    # One of them is Nitrate/Nitrite, to be sure the keywords
    ${service_uid1} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  s1  title=Nitrate/Nitrite  Keyword=NitrateNitrite  Category=${cat_uid}
    ${service_uid2} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  s2  title=Ammonia  Keyword=ammonia  Category=${cat_uid}
    # And then create a new AR with just these two services.
    # We'll set the ClientSampleID to match the first valid result in the XLSX.
    ${ar_uid} =  Create AR  /clients/client-1  analyses=${service_uid1},${service_uid2}  SampleType=${st_uid}   ClientSampleID=A00036896008
    do action for  ${ar_uid}  receive
    debug
    # Create a worksheet
    # Add all the analyses from our test AR to the new worksheet
    # Do the export!
    Go to  ${PLONEURL}
    Click Link  Import
    Wait until page contains  Select a data interface
    Select from list  exim  Lachat QuickChem FIA
    # This instrument supports only CSV
    Element Should Contain  lachat_quickchem_fia_format  CSV
    ${PATH_TO_TEST} =  run keyword  resource_filename
    Choose File  lachat_quickchem_fia_file  ${PATH_TO_TEST}/files/QuickChemFIA.csv
    Click Button  Submit
    Wait until page contains  Log trace
    # Only one AR (two analyses) should have been imported!
    page should contain  End of file reached successfully: 20 objects, 3 analyses, 549 results
    page should contain  ST-0001-R01: ['Analysis NitrateNitrite', 'Analysis ammonia'] imported sucessfully
    page should contain  Import finished successfully: 1 ARs and 2 results updated
    # And we must verify that the results are valid
    go to    ${PLONEURL}/clients/client-1/ST-0001-R01/manage_results
    textfield value should be  css=[selector="Result_ammonia"]  1.68
    textfield value should be  css=[selector="Result_NitrateNitrite"]  11.58


Test Lachat QuickChem FIA Importer
    Enable autologin as  LabManager
    set autologin username  test_labmanager
    # Requirements for creating services and ARs:
    ${cat_uid} =  Create Object  bika_setup/bika_analysiscategories  AnalysisCategory  c1  title=test
    ${st_uid} =  Create Object   bika_setup/bika_sampletypes  SampleType  ST1  title=Sample Type   Prefix=ST
    # I will just test two services for a single sample.
    # One of them is Nitrate/Nitrite, to be sure the keywords
    ${service_uid1} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  s1  title=Nitrate/Nitrite  Keyword=NitrateNitrite  Category=${cat_uid}
    ${service_uid2} =  Create Object  bika_setup/bika_analysisservices  AnalysisService  s2  title=Ammonia  Keyword=ammonia  Category=${cat_uid}
    # And then create a new AR with just these two services.
    # We'll set the ClientSampleID to match the first valid result in the XLSX.
    ${ar_uid} =  Create AR  /clients/client-1  analyses=${service_uid1},${service_uid2}  SampleType=${st_uid}   ClientSampleID=A00036896008
    do action for  ${ar_uid}  receive
    # Do the import!
    Go to  ${PLONEURL}
    Click Link  Import
    Wait until page contains  Select a data interface
    Select from list  exim  Lachat QuickChem FIA
    # This instrument supports only CSV
    Element Should Contain  lachat_quickchem_fia_format  CSV
    ${PATH_TO_TEST} =  run keyword  resource_filename
    Choose File  lachat_quickchem_fia_file  ${PATH_TO_TEST}/files/QuickChemFIA.csv
    Click Button  Submit
    Wait until page contains  Log trace
    # Only one AR (two analyses) should have been imported!
    page should contain  End of file reached successfully: 20 objects, 3 analyses, 549 results
    page should contain  ST-0001-R01: ['Analysis NitrateNitrite', 'Analysis ammonia'] imported sucessfully
    page should contain  Import finished successfully: 1 ARs and 2 results updated
    # And we must verify that the results are valid
    go to    ${PLONEURL}/clients/client-1/ST-0001-R01/manage_results
    textfield value should be  css=[selector="Result_ammonia"]  1.68
    textfield value should be  css=[selector="Result_NitrateNitrite"]  11.58

*** Keywords ***

Start browser
    Open browser                        ${PLONEURL}  chrome
    Set selenium speed                  ${SELENIUM_SPEED}
