from create_AIFM import create_aifm
from create_AIF import create_aif

# Documentation:
# all docs in H:\Compliance\AIFMD\
# FCA Guidlines.pdf: Description and example for the fields using text
# AIFMSample.xml: sample XML file for AIFM report
# AIFSample.xml: sample XML file for AIF report
# 20211231 Ananda AIFMDReturns - 2 Funds - Buzzacot output.xlsm -> readable excel file from Buzacot - the model seems to come from the FCA/ESMA
# 2013-1358_aifmd_reporting_it_technical_guidance-Revision4.xlsx -> Technical Guidance for each field
# AIFMD_REPORTING_DataTypes_V1.2.xsd: structure of the XML Document


if __name__ == '__main__':
    create_aifm()
    create_aif('ALTO')
    # create_aif('NEUTRAL')

