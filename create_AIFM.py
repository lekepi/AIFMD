from datetime import date, datetime
from models import engine, session, NameValue
from utils import previous_quarter
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree
import pandas as pd
from utils import prettify, simple_email, list_to_html_table
from manual_data import EURUSD_RATE

# XML: http://pymotw.com/2/xml/etree/ElementTree/create.html

security_country_list = ['United States', 'Canada', 'Switzerland']

def create_aifm():

    my_date = date.today()
    # my_date = date(2022, 4, 1)

    quarter, start_date, end_date = previous_quarter(my_date)
    year = start_date.year
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    inv_manager_data = session.query(NameValue).filter(NameValue.name.startswith('im_')).order_by(NameValue.name.desc()).all()
    AIFMName_value = [val.my_value for val in inv_manager_data if val.name == 'im_name'][0]
    AIFMNationalCode_value = [val.my_value for val in inv_manager_data if val.name == 'im_fca_code'][0]
    AIFMIdentifierLEI_value = [val.my_value for val in inv_manager_data if val.name == 'im_lei'][0]

    my_sql = f"""SELECT T2.ticker,if(T2.isin is Null,'NA',T2.isin) as isin,T2.name,macro_code,macro_label,asset_label,asset_code,subasset_label,
                    subasset_code,round(abs(mkt_value_usd),0) as notional_usd,
                    if(mkt_value_usd>=0,'L','S') as side,T2.prod_type,T2.mic,T4.name as country,T4.continent,T1.parent_fund_id FROM position T1 
                    JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                    JOIN country T4 on T3.country_id=T4.id JOIN aifmd T5 on T5.id=T2.aifmd_exposure_id
                    WHERE T1.entry_date='{end_date}' and parent_fund_id in (1,3,5) order by round(abs(mkt_value_usd),0) desc"""
    df_temp = pd.read_sql(my_sql, con=engine)

    df_aggr_cfd = df_temp.loc[~(df_temp['country'].isin(security_country_list)) & (df_temp['prod_type'] == 'Cash')]
    df_aggr_cfd['macro_code'] = 'DER'
    df_aggr_cfd['macro_label'] = 'Derivatives'
    df_aggr_cfd['asset_code'] = 'DER_EQD'
    df_aggr_cfd['asset_label'] = 'Equity derivatives'
    df_aggr_cfd['subasset_code'] = 'DER_EQD_OTHD'
    df_aggr_cfd['subasset_label'] = 'Other equity derivatives'
    df_aggr_cfd['mic'] = 'XXXX'

    df_aggr_other = df_temp.loc[(df_temp['country'].isin(security_country_list)) | (df_temp['prod_type'] != 'Cash')]
    df_aggr = pd.merge(df_aggr_cfd, df_aggr_other, how='outer')

    df_aggr.to_excel(fr'H:\Compliance\AIFMD\KEY FILES\Historic\All Positions AIFM {end_date_str}.xlsx')

    total_usd = df_aggr['notional_usd'].sum()
    AUM_USD = int(total_usd)

    tree = ElementTree("tree")

    root = Element('AIFMReportingInfo', {'CreationDateAndTime': f'{now_str}',
                                         'Version': '2.0',
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

    LastReportingFlag = SubElement(AIFMRecordInfo, 'LastReportingFlag')
    LastReportingFlag.text = 'false'

    AIFMReportingCode_value = ('5', '"Authorised AIFM with quarterly obligation " under Article 7')
    AIFMReportingCode = SubElement(AIFMRecordInfo, 'AIFMReportingCode')
    AIFMReportingCode.text = AIFMReportingCode_value[0]  # "Authorised AIFM with quarterly obligation " under Article 7
    table_main.append(['16', 'Reporting Code', f'{AIFMReportingCode_value[0]}: {AIFMReportingCode_value[1]}'])

    AIFMJurisdiction_value = 'GB'
    AIFMJurisdiction = SubElement(AIFMRecordInfo, 'AIFMJurisdiction')
    AIFMJurisdiction.text = AIFMJurisdiction_value
    table_main.append(['17', 'Jurisdiction', AIFMJurisdiction_value])

    AIFMNationalCode = SubElement(AIFMRecordInfo, 'AIFMNationalCode')
    AIFMNationalCode.text = AIFMNationalCode_value
    table_main.append(['18', 'National Code', AIFMNationalCode_value])

    AIFMName = SubElement(AIFMRecordInfo, 'AIFMName')
    AIFMName.text = AIFMName_value
    table_main.append(['19', 'Name', AIFMName_value])

    AIFMNoReportingFlag_value = 'false'
    AIFMNoReportingFlag = SubElement(AIFMRecordInfo, 'AIFMNoReportingFlag')
    AIFMNoReportingFlag.text = AIFMNoReportingFlag_value
    table_main.append(['21', 'AIFM No Reporting Flag', AIFMNoReportingFlag_value])

    AIFMCompleteDescription = SubElement(AIFMRecordInfo, 'AIFMCompleteDescription')
    AIFMIdentifier = SubElement(AIFMCompleteDescription, 'AIFMIdentifier')
    AIFMIdentifierLEI = SubElement(AIFMIdentifier, 'AIFMIdentifierLEI')
    AIFMIdentifierLEI.text = AIFMIdentifierLEI_value
    table_main.append(['22', 'LEI', AIFMIdentifierLEI_value])

    html += list_to_html_table(table_main, 'Header and Description')

    # 5 biggest markets (take only listed, not OTC)
    table_top_markets = [['Rank', 'Code', 'Aggr Value Eur']]
    AIFMPrincipalMarkets = SubElement(AIFMCompleteDescription, 'AIFMPrincipalMarkets')

    # Aggregated Value by Market
    df_market = df_aggr.groupby(['mic'], as_index=False)[['notional_usd']].sum()
    df_market.sort_values(by='notional_usd', ascending=False, inplace=True)
    df_market = df_market[:5]
    df_market = df_market.reset_index()

    for index, row in df_market.iterrows():
        AIFMFivePrincipalMarket = SubElement(AIFMPrincipalMarkets, 'AIFMFivePrincipalMarket')
        Ranking_value = str(index + 1)
        Ranking = SubElement(AIFMFivePrincipalMarket, 'Ranking')
        Ranking.text = Ranking_value
        MarketIdentification = SubElement(AIFMFivePrincipalMarket, 'MarketIdentification')
        MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
        if row['mic'] == 'XXXX':
            MarketCodeType_value = 'OTC'
            MarketCodeType.text = MarketCodeType_value
            MarketCode_value = 'NA'
        else:
            MarketCodeType_value = 'MIC'
            MarketCodeType.text = MarketCodeType_value
            MarketCode_value = row['mic']
            MarketCode = SubElement(MarketIdentification, 'MarketCode')
            MarketCode.text = MarketCode_value
        AggregatedValueAmount_value = str(int(row['notional_usd']/EURUSD_RATE))
        AggregatedValueAmount = SubElement(AIFMFivePrincipalMarket, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value
        table_top_markets.append([Ranking_value, f'{MarketCodeType_value} - {MarketCode_value}', AggregatedValueAmount_value])

    rows_num = len(df_market.index)
    if rows_num < 5:
        for i in range(rows_num + 1, 6):
            AIFMFivePrincipalMarket = SubElement(AIFMPrincipalMarkets, 'AIFMFivePrincipalMarket')
            Ranking_value = str(i)
            Ranking = SubElement(AIFMFivePrincipalMarket, 'Ranking')
            Ranking.text = Ranking_value
            MarketIdentification = SubElement(AIFMFivePrincipalMarket, 'MarketIdentification')
            MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
            MarketCodeType.text = 'NOT'
            table_top_markets.append([Ranking_value, 'NOT', ''])


    html += list_to_html_table(table_top_markets, 'Five Principal Markets (N26-29)')

    # 5 Biggest AIFM Assets
    table_top_assets = [['Rank', 'SubAsset Type Code', 'SubAsset Type Label', 'Aggr Value Eur']]
    AIFMPrincipalInstruments = SubElement(AIFMCompleteDescription, 'AIFMPrincipalInstruments')

    df_big_assets = df_aggr.groupby(['subasset_label', 'subasset_code'], as_index=False)[['notional_usd']].sum()

    if not df_big_assets.empty:
        df_big_assets.sort_values(by='notional_usd', ascending=False, inplace=True)
        df_big_assets = df_big_assets[:5]
        df_big_assets = df_big_assets.reset_index()

        for index, row in df_big_assets.iterrows():
            AIFMPrincipalInstrument = SubElement(AIFMPrincipalInstruments, 'AIFMPrincipalInstrument')
            Ranking_value = str(index + 1)
            Ranking = SubElement(AIFMPrincipalInstrument, 'Ranking')
            Ranking.text = Ranking_value
            SubAssetType_value = row['subasset_code']
            SubAssetType_label = row['subasset_label']
            SubAssetType = SubElement(AIFMPrincipalInstrument, 'SubAssetType')
            SubAssetType.text = SubAssetType_value
            AggregatedValueAmount_value = str(int(row['notional_usd']/EURUSD_RATE))
            AggregatedValueAmount = SubElement(AIFMPrincipalInstrument, 'AggregatedValueAmount')
            AggregatedValueAmount.text = AggregatedValueAmount_value
            table_top_assets.append([Ranking_value, SubAssetType_value, SubAssetType_label, AggregatedValueAmount_value])

        rows_num = len(df_big_assets.index)
        if rows_num < 5:
            for i in range(rows_num + 1, 6):
                AIFMPrincipalInstrument = SubElement(AIFMPrincipalInstruments, 'AIFMPrincipalInstrument')
                Ranking_value = str(i)
                Ranking = SubElement(AIFMPrincipalInstrument, 'Ranking')
                Ranking.text = Ranking_value
                SubAssetType_value = 'NTA_NTA_NOTA'
                SubAssetType = SubElement(AIFMPrincipalInstrument, 'SubAssetType')
                SubAssetType.text = SubAssetType_value
                table_top_assets.append([Ranking_value, SubAssetType_value, '', ''])

    html += list_to_html_table(table_top_assets, 'Five Principal Instruments (N30-32)')

    table_AUM = [['Field', 'Value']]
    aum_usd = str(int(AUM_USD))
    aum_eur = str(int(AUM_USD / EURUSD_RATE))
    AUMAmountInEuro = SubElement(AIFMCompleteDescription, 'AUMAmountInEuro')
    AUMAmountInEuro.text = aum_eur
    AIFMBaseCurrencyDescription = SubElement(AIFMCompleteDescription, 'AIFMBaseCurrencyDescription')
    BaseCurrency = SubElement(AIFMBaseCurrencyDescription, 'BaseCurrency')
    BaseCurrency.text = 'USD'
    AUMAmountInBaseCurrency = SubElement(AIFMBaseCurrencyDescription, 'AUMAmountInBaseCurrency')
    AUMAmountInBaseCurrency.text = str(aum_usd)
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
    # with open(xml_filename, "w") as f:
    #    f.write(output)

    tree._setroot(root)
    tree.write(xml_filename, encoding="UTF-8", xml_declaration=True)

    simple_email(f"AIFM Report {quarter} {year}", '', 'olivier@ananda-am.com', html, xml_filename)
