from datetime import date, datetime
from models import engine
from utils import previous_quarter
from xml.etree.ElementTree import Element, SubElement, Comment
import pandas as pd
from utils import prettify, simple_email, list_to_html_table
from manual_data import EURUSD_RATE, AUM_ALTO_USD, AUM_NEUTRAL_USD

# XML: http://pymotw.com/2/xml/etree/ElementTree/create.html


def create_aifm():

    today = date.today()
    quarter, start_date, end_date = previous_quarter(today)
    year = start_date.year
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    root = Element('AIFMReportingInfo', {'CreationDateAndTime': f'{now_str}',
                                         'Version': '1.2',
                                         'ReportingMemberState': 'GB',
                                         'xsi:noNamespaceSchemaLocation': 'AIFMD_DATMAN_V1.2.xsd',
                                         'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})

    comment = Comment('AIFM Report')
    root.append(comment)
    table_main = [['N', 'Description', 'Value']]
    html = ''
    AIFMRecordInfo = SubElement(root, 'AIFMRecordInfo')

    FilingType_value = ['INIT', 'initial reporting for the reporting period']
    FilingType = SubElement(AIFMRecordInfo, 'FilingType')
    FilingType.text = FilingType_value[0]
    table_main.append(['4', 'Filing Type', f'{FilingType_value[0]}: {FilingType_value[1]}'])

    AIFMContentType_value = ['1', '24(1) reporting contents for all AIFs managed']
    AIFMContentType = SubElement(AIFMRecordInfo, 'AIFMContentType')
    AIFMContentType.text = AIFMContentType_value[0]
    table_main.append(['5', 'Content Type', AIFMContentType_value[1]])

    ReportingPeriodStartDate = SubElement(AIFMRecordInfo, 'ReportingPeriodStartDate')
    ReportingPeriodStartDate.text = start_date_str
    table_main.append(['6', 'Reporting Start Date', start_date_str])
    ReportingPeriodEndDate = SubElement(AIFMRecordInfo, 'ReportingPeriodEndDate')
    ReportingPeriodEndDate.text = end_date_str
    table_main.append(['7', 'Reporting End Date', end_date_str])
    ReportingPeriodType = SubElement(AIFMRecordInfo, "ReportingPeriodType")
    ReportingPeriodType.text = quarter
    table_main.append(['8', 'Reporting Period Type', quarter])
    ReportingPeriodYear = SubElement(AIFMRecordInfo, 'ReportingPeriodYear')
    ReportingPeriodYear.text = str(year)
    table_main.append(['9', 'Reporting Period Year', str(year)])

    # <AIFMReportingObligationChangeFrequencyCode> Optional
    # <AIFMReportingObligationChangeContentsCode> Optional
    # <AIFMReportingObligationChangeQuarter> Forbidden if both above not there

    LastReportingFlag = SubElement(AIFMRecordInfo, 'LastReportingFlag')
    LastReportingFlag.text = 'false'

    # <QuestionNumber> and <AssumptionDescription> not used here (so <Assumptions>, <Assumption> the parents are not too)

    AIFMReportingCode_value = ('5', '"Authorised AIFM with quarterly obligation " under Article 7')
    AIFMReportingCode = SubElement(AIFMRecordInfo, 'AIFMReportingCode')
    AIFMReportingCode.text = AIFMReportingCode_value[0]  # "Authorised AIFM with quarterly obligation " under Article 7
    table_main.append(['16', 'Reporting Code', f'{AIFMReportingCode_value[0]}: {AIFMReportingCode_value[1]}'])

    AIFMJurisdiction_value = 'GB'
    AIFMJurisdiction = SubElement(AIFMRecordInfo, 'AIFMJurisdiction')
    AIFMJurisdiction.text = AIFMJurisdiction_value
    table_main.append(['17', 'Jurisdiction', AIFMJurisdiction_value])

    AIFMNationalCode_value = '924813'
    AIFMNationalCode = SubElement(AIFMRecordInfo, 'AIFMNationalCode')
    AIFMNationalCode.text = AIFMNationalCode_value
    table_main.append(['18', 'National Code', AIFMNationalCode_value])

    AIFMName_value = 'Ananda Asset Management Limited'
    AIFMName = SubElement(AIFMRecordInfo, 'AIFMName')
    AIFMName.text = AIFMName_value
    table_main.append(['19', 'Name', AIFMName_value])

    AIFMEEAFlag_value = 'true'
    AIFMEEAFlag = SubElement(AIFMRecordInfo, 'AIFMEEAFlag')
    AIFMEEAFlag.text = AIFMEEAFlag_value
    table_main.append(['20', 'AIFM EEA Flag', AIFMEEAFlag_value])

    AIFMNoReportingFlag_value = 'false'
    AIFMNoReportingFlag = SubElement(AIFMRecordInfo, 'AIFMNoReportingFlag')
    AIFMNoReportingFlag.text = AIFMNoReportingFlag_value
    table_main.append(['21', 'AIFM No Reporting Flag', AIFMNoReportingFlag_value])

    AIFMCompleteDescription = SubElement(AIFMRecordInfo, 'AIFMCompleteDescription')
    AIFMIdentifier = SubElement(AIFMCompleteDescription, 'AIFMIdentifier')
    AIFMIdentifierLEI_value = '213800UUU8A1Z4WJ8L67'
    AIFMIdentifierLEI = SubElement(AIFMIdentifier, 'AIFMIdentifierLEI')
    AIFMIdentifierLEI.text = AIFMIdentifierLEI_value
    table_main.append(['22', 'LEI', AIFMIdentifierLEI_value])

    html += list_to_html_table(table_main, 'Header and Description')

    # 5 biggest markets (take only listed, not OTC)
    table_top_markets = [['Rank', 'Code', 'Aggr Value Eur']]
    AIFMPrincipalMarkets = SubElement(AIFMCompleteDescription, 'AIFMPrincipalMarkets')
    AIFMFivePrincipalMarket = SubElement(AIFMPrincipalMarkets, 'AIFMFivePrincipalMarket')

    my_sql = f"""SELECT mic,abs(sum(mkt_value_usd))/{EURUSD_RATE} as aggr_value FROM anandaprod.position T1 
                 JOIN Product T2 on T1.product_id=T2.id
                 WHERE T1.entry_date='{end_date}' 
                 and parent_fund_id in (1,3)
                 group by mic order by abs(sum(mkt_value_usd)) desc LIMIT 5;"""

    df = pd.read_sql(my_sql, con=engine)

    for index, row in df.iterrows():
        Ranking_value = str(index + 1)
        Ranking = SubElement(AIFMFivePrincipalMarket, 'Ranking')
        Ranking.text = Ranking_value
        MarketIdentification = SubElement(AIFMFivePrincipalMarket, 'MarketIdentification')
        MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
        MarketCodeType.text = 'MIC'
        MarketCode_value = row['mic']
        MarketCode = SubElement(MarketIdentification, 'MarketCode')
        MarketCode.text = MarketCode_value
        AggregatedValueAmount_value = str(int(row['aggr_value']))
        AggregatedValueAmount = SubElement(AIFMFivePrincipalMarket, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value

        table_top_markets.append([Ranking_value, MarketCode_value, AggregatedValueAmount_value])
    html += list_to_html_table(table_top_markets, 'Five Principal Markets (N26-29)')

    # 5 Biggest AIFM Assets
    table_top_assets = [['Rank', 'SubAsset Type', 'Aggr Value Eur']]
    AIFMPrincipalInstruments = SubElement(AIFMCompleteDescription, 'AIFMPrincipalInstruments')
    # TODO make sure we should include the FX trades
    my_sql = f"""((SELECT subasset_label,subasset_code,abs(sum(mkt_value_usd))/{EURUSD_RATE} as aggr_value FROM anandaprod.position T1 
                 JOIN Product T2 on T1.product_id=T2.id
                 JOIN aifmd T4 on T4.id=T2.aifmd_exposure_id
                 WHERE T1.entry_date='{end_date}' 
                 and parent_fund_id in (1,3)
                 group by subasset_label order by abs(sum(mkt_value_usd)) desc)
                 UNION
                 (SELECT subasset_label,subasset_code,sum(abs(notional_USD))/{EURUSD_RATE} as aggr_value FROM position_pb T1 JOIN Product T2 on T1.product_id=T2.id 
                 JOIN aifmd T4 on T4.id=T2.aifmd_exposure_id
                 WHERE T1.entry_date='{end_date}' and prod_type='FX Forward'
                 GROUP BY subasset_label)) ORDER BY aggr_value desc LIMIT 5;"""

    df = pd.read_sql(my_sql, con=engine)

    for index, row in df.iterrows():
        AIFMPrincipalInstrument = SubElement(AIFMPrincipalInstruments, 'AIFMPrincipalInstrument')
        Ranking_value = str(index + 1)
        Ranking = SubElement(AIFMPrincipalInstrument, 'Ranking')
        Ranking.text = Ranking_value
        SubAssetType_value = row['subasset_code']
        SubAssetType_label = row['subasset_label']
        SubAssetType = SubElement(AIFMPrincipalInstrument, 'SubAssetType')
        SubAssetType.text = SubAssetType_value
        AggregatedValueAmount_value = str(int(row['aggr_value']))
        AggregatedValueAmount = SubElement(AIFMPrincipalInstrument, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value
        table_top_assets.append([Ranking_value, SubAssetType_label, AggregatedValueAmount_value])

    html += list_to_html_table(table_top_assets, 'Five Principal Instruments (N30-32)')

    table_AUM = [['Field', 'Value']]
    aum_usd = str(int(AUM_ALTO_USD + AUM_NEUTRAL_USD))
    aum_eur = str(int((AUM_ALTO_USD + AUM_NEUTRAL_USD) / EURUSD_RATE))
    AUMAmountInEuro = SubElement(AIFMCompleteDescription, 'AUMAmountInEuro')
    AUMAmountInEuro.text = aum_eur
    AIFMBaseCurrencyDescription = SubElement(AIFMCompleteDescription, 'AIFMBaseCurrencyDescription')
    BaseCurrency = SubElement(AIFMBaseCurrencyDescription, 'BaseCurrency')
    BaseCurrency.text = 'USD'
    AUMAmountInBaseCurrency = SubElement(AIFMBaseCurrencyDescription, 'AUMAmountInBaseCurrency')
    AUMAmountInBaseCurrency.text = aum_usd
    FXEURReferenceRateType = SubElement(AIFMBaseCurrencyDescription, 'FXEURReferenceRateType')
    FXEURReferenceRateType.text = 'ECB'
    FXEURRate_value = str(EURUSD_RATE)
    FXEURRate = SubElement(AIFMBaseCurrencyDescription, 'FXEURRate')
    FXEURRate.text = FXEURRate_value

    table_AUM.append(["AUM USD", aum_usd])
    table_AUM.append(["AUM EUR", aum_eur])
    table_AUM.append(["FX EUR Rate", FXEURRate_value])
    html += list_to_html_table(table_AUM, 'AUM (N33-38)')

    output = prettify(root)

    xml_filename = "AIFM.xml"
    with open(xml_filename, "w") as f:
        f.write(output)

    simple_email(f"AIFM Report {quarter} {year}", '', 'olivier@ananda-am.com', html, xml_filename)
