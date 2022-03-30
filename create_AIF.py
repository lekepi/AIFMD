from datetime import date, datetime
from utils import previous_quarter, simple_email
from xml.etree.ElementTree import Element, SubElement, Comment
from utils import prettify, list_to_html_table, find_active_contract
from manual_data import EURUSD_RATE, AUM_ALTO_USD, AUM_NEUTRAL_USD, \
    NAV_ALTO_USD, NAV_NEUTRAL_USD, MainBeneficialOwnersRate_value_alto, MainBeneficialOwnersRate_value_neutral
import pandas as pd
from models import engine


alto_dict = {'AIF National Code': '831291',
             'AIF Name': 'Ananda Long Term Opportunities Fund Ltd',
             'Inception Date': '2019-01-18',
             'AIF Name': 'Ananda Long Term Opportunities Fund Ltd',
             'AIF Identifier LEI': '213800NAN6UMJLZTEC57'}

neutral_dict = {'AIF National Code': '940433',
                'AIF Name': 'Ananda Market Neutral Fund Ltd',
                'Inception Date': '2020-12-01',
                'AIF Name': 'Ananda Market Neutral Fund Ltd',
                'AIF Identifier LEI': '213800ISEVE64OOWY481'}

# name and ISIN:
alto_share_classes = [['Class A Shares USD', None],
                    ['Class F Shares USD', 'KYG0417S1167'],
                    ['Class L Shares USD', None],
                    ['Class A Shares EUR', None],
                    ['Class F Shares EUR', 'KYG0417S1084'],
                    ['Class L Shares EUR', 'KYG0417S1324'],
                    ['Class A Shares GBP', None],
                    ['Class F Shares GBP', 'KYG0417S1241'],
                    ['Class L Shares GBP', None]]

neutral_share_classes = [['Class A shares', None],
                         ['Class B shares', None],
                         ['Class C shares', None],
                         ['Class D shares', None]]

alto_pbs = [['Goldman Sachs International', 'N9FYJ29MC81JI74MJE92'],
            ['MORGAN STANLEY & CO. INTERNATIONAL PLC', '4PQUHN3JPFGFNF3BB653']]

neutral_pbs = [['Goldman Sachs International', 'N9FYJ29MC81JI74MJE92'],
               ['MORGAN STANLEY & CO. INTERNATIONAL PLC', '4PQUHN3JPFGFNF3BB653']]


def create_aif(my_fund):

    if my_fund == 'ALTO':
        aif_dict = alto_dict
        share_classes = alto_share_classes
        pbs = alto_pbs
        AUM_USD = AUM_ALTO_USD
        NAV_USD = NAV_ALTO_USD
        fund_id = 1
        MainBeneficialOwnersRate_value = str(MainBeneficialOwnersRate_value_alto)
        Investment_strategy = ['EQTY_LGBS', 'Equity: Long Bias']
    elif my_fund == 'NEUTRAL':
        aif_dict = neutral_dict
        share_classes = neutral_share_classes
        pbs = neutral_pbs
        AUM_USD = AUM_NEUTRAL_USD
        NAV_USD = NAV_NEUTRAL_USD
        fund_id = 3
        MainBeneficialOwnersRate_value = str(MainBeneficialOwnersRate_value_neutral)
        Investment_strategy = ['EQTY_MTNL', 'Equity: Market neutral']

    today = date.today()
    quarter, start_date, end_date = previous_quarter(today)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    year = start_date.year

    root = Element('AIFReportingInfo', {'CreationDateAndTime': f'{now_str}',
                                         'Version': '1.2',
                                         'ReportingMemberState': 'GB',
                                         'xsi:noNamespaceSchemaLocation': 'AIFMD_DATMAN_V1.2.xsd',
                                         'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})
    comment = Comment(f'AIF Report {my_fund}')
    root.append(comment)
    table_main = [['N', 'Description', 'Value']]
    html = f'<H2>24.1 for {my_fund}<H2>'
    AIFRecordInfo = SubElement(root, 'AIFRecordInfo')
    FilingType_value = ['INIT', 'initial reporting for the reporting period']
    FilingType = SubElement(AIFRecordInfo, 'FilingType')
    FilingType.text = FilingType_value[0]
    table_main.append(['4', 'Filing Type', f'{FilingType_value[0]}: {FilingType_value[1]}'])

    AIFContentType_value = ['4', '24(1) + 24(2) + 24(4) reporting obligation']
    AIFContentType = SubElement(AIFRecordInfo, 'AIFContentType')
    AIFContentType.text = AIFContentType_value[0]
    table_main.append(['5', 'Content Type', f'{AIFContentType_value[0]}: {AIFContentType_value[1]}'])

    ReportingPeriodStartDate = SubElement(AIFRecordInfo, 'ReportingPeriodStartDate')
    ReportingPeriodStartDate.text = start_date_str
    table_main.append(['6', 'Reporting Start Date', start_date_str])
    ReportingPeriodEndDate = SubElement(AIFRecordInfo, 'ReportingPeriodEndDate')
    ReportingPeriodEndDate.text = end_date_str
    table_main.append(['7', 'Reporting End Date', end_date_str])
    ReportingPeriodType = SubElement(AIFRecordInfo, "ReportingPeriodType")
    ReportingPeriodType.text = quarter
    table_main.append(['8', 'Reporting Period Type', quarter])
    ReportingPeriodYear = SubElement(AIFRecordInfo, 'ReportingPeriodYear')
    ReportingPeriodYear.text = str(year)
    table_main.append(['9', 'Reporting Period Year', str(year)])

    # <AIFReportingObligationChangeFrequencyCode> Optional
    # <AIFReportingObligationChangeContentsCode> Optional
    # <AIFReportingObligationChangeQuarter> Forbidden if both above not there

    LastReportingFlag = SubElement(AIFRecordInfo, 'LastReportingFlag')
    LastReportingFlag.text = 'false'

    # <QuestionNumber> and <AssumptionDescription> not used here (so <Assumptions>, <Assumption> the parents are not too)

    AIFMNationalCode_value = '924813'
    AIFMNationalCode = SubElement(AIFRecordInfo, 'AIFMNationalCode')
    AIFMNationalCode.text = AIFMNationalCode_value
    table_main.append(['16', 'AIFM National Code', AIFMNationalCode_value])

    AIFNationalCode_value = aif_dict['AIF National Code']
    AIFNationalCode = SubElement(AIFRecordInfo, 'AIFNationalCode')
    AIFNationalCode.text = AIFNationalCode_value
    table_main.append(['17', 'AIF National Code', AIFNationalCode_value])

    AIFName_value = aif_dict['AIF Name']
    AIFName = SubElement(AIFRecordInfo, 'AIFMName')
    AIFName.text = AIFName_value
    table_main.append(['18', 'Name', AIFName_value])

    AIFEEAFlag_value = 'false'
    AIFEEAFlag = SubElement(AIFRecordInfo, 'AIFEEAFlag')
    AIFEEAFlag.text = AIFEEAFlag_value
    table_main.append(['19', 'AIF EEA Flag', AIFEEAFlag_value])

    # https://www.esma.europa.eu/document/tables-8-9-10-annex-2-esma-guidelines-aifmd-reporting-obligation-revised
    # Annex II - Table 9.
    AIFReportingCode_value = ['30', 'Authorised AIFM with quarterly obligation']
    AIFReportingCode = SubElement(AIFRecordInfo, 'AIFReportingCode')
    AIFReportingCode.text = AIFReportingCode_value[0]
    table_main.append(['20', 'AIF Reporting Code', f'table-9-annex-2, {AIFReportingCode_value[0]}: {AIFReportingCode_value[1]}'])

    # ISO 3166
    AIFDomicile_value = ['KY', 'Cayman Islands']
    AIFDomicile = SubElement(AIFRecordInfo, 'AIFDomicile')
    AIFDomicile.text = AIFDomicile_value[0]
    table_main.append(['21', 'AIF Domicile', f'ISO 3166, {AIFDomicile_value[0]}: {AIFDomicile_value[1]}'])

    InceptionDate_value = aif_dict['Inception Date']
    InceptionDate = SubElement(AIFRecordInfo, 'InceptionDate')
    InceptionDate.text = InceptionDate_value
    table_main.append(['22', 'Inception Date', InceptionDate_value])

    AIFNoReportingFlag_value = 'false'
    AIFNoReportingFlag = SubElement(AIFRecordInfo, 'AIFNoReportingFlag')
    AIFNoReportingFlag.text = AIFNoReportingFlag_value
    table_main.append(['23', 'AIF No Reporting Flag', AIFNoReportingFlag_value])

    AIFCompleteDescription = SubElement(AIFRecordInfo, 'AIFCompleteDescription')
    AIFPrincipalInfo = SubElement(AIFCompleteDescription, 'AIFPrincipalInfo')
    AIFIdentification = SubElement(AIFPrincipalInfo, 'AIFIdentification')
    AIFIdentifierLEI_value = aif_dict['AIF Identifier LEI']
    AIFIdentifierLEI = SubElement(AIFIdentification, 'AIFIdentifierLEI')
    AIFIdentifierLEI.text = AIFIdentifierLEI_value
    table_main.append(['24', 'LEI', AIFIdentifierLEI_value])

    ShareClassFlag_value = 'true'
    ShareClassFlag = SubElement(AIFPrincipalInfo, 'ShareClassFlag')
    ShareClassFlag.text = ShareClassFlag_value
    table_main.append(['33', 'Share Class Flag', ShareClassFlag_value])

    html += list_to_html_table(table_main, 'Header and Description')


    table_share_class = [['National Code', 'Isin', 'Name']]

    for share_class in share_classes:
        ShareClassIdentification = SubElement(AIFPrincipalInfo, 'ShareClassIdentification')
        ShareClassNationalCode_name = share_class[0]
        ShareClassNationalCode = SubElement(ShareClassIdentification, 'ShareClassNationalCode')
        ShareClassNationalCode.text = ShareClassNationalCode_name

        ShareClassNationalCode_isin = share_class[1]
        if ShareClassNationalCode_isin:
            ShareClassIdentifierISIN = SubElement(ShareClassIdentification, 'ShareClassIdentifierISIN')
            ShareClassIdentifierISIN.text = ShareClassNationalCode_isin

        ShareClassName = SubElement(ShareClassIdentification, 'ShareClassName')
        ShareClassName.text = ShareClassNationalCode_name

        table_share_class.append([ShareClassNationalCode_name, ShareClassNationalCode_isin, ShareClassNationalCode_name])

    html += list_to_html_table(table_share_class, 'Share Classes (N34-40)')

    AIFDescription = SubElement(AIFPrincipalInfo, 'AIFDescription')
    AIFMasterFeederStatus_value ='NONE'
    AIFMasterFeederStatus = SubElement(AIFDescription, 'AIFMasterFeederStatus')
    AIFMasterFeederStatus.text = AIFMasterFeederStatus_value

    html += f"<H4>41) AIF Master Feeder Status : {AIFMasterFeederStatus_value}</H4>"

    PrimeBrokers = SubElement(AIFDescription, 'PrimeBrokers')
    PrimeBrokerIdentification = SubElement(PrimeBrokers, 'PrimeBrokerIdentification')

    table_pb = [['Entity Name', 'LEI']]
    for pb in pbs:
        EntityName_value = pb[0]
        EntityName = SubElement(PrimeBrokerIdentification, 'EntityName')
        EntityName.text = EntityName_value

        EntityIdentificationLEI_value = pb[1]
        EntityIdentificationLEI = SubElement(PrimeBrokerIdentification, 'EntityIdentificationLEI')
        EntityIdentificationLEI.text = EntityIdentificationLEI_value

        table_pb.append(
            [EntityName_value, EntityIdentificationLEI_value])
    html += list_to_html_table(table_pb, 'Prime Brokers (N45-47)')

    table_from_base_cncy = [['N', 'Description', 'Value']]

    AIFBaseCurrencyDescription = SubElement(AIFDescription, 'AIFBaseCurrencyDescription')

    AUMAmountInBaseCurrency_value = str(AUM_USD)
    AUMAmountInBaseCurrency = SubElement(AIFBaseCurrencyDescription, 'AUMAmountInBaseCurrency')
    AUMAmountInBaseCurrency.text = AUMAmountInBaseCurrency_value
    table_from_base_cncy.append(['48', 'AUM Amount In Base Currency', AUMAmountInBaseCurrency_value])

    BaseCurrency_value = 'USD'
    BaseCurrency = SubElement(AIFBaseCurrencyDescription, 'BaseCurrency')
    BaseCurrency.text = BaseCurrency_value
    table_from_base_cncy.append(['49', 'Base Currency', BaseCurrency_value])

    FXEURReferenceRateType_value = 'ECB'
    FXEURReferenceRateType = SubElement(AIFBaseCurrencyDescription, 'FXEURReferenceRateType')
    FXEURReferenceRateType.text = FXEURReferenceRateType_value
    table_from_base_cncy.append(['50', 'FX EUR Reference Rate Type', FXEURReferenceRateType_value])

    FXEURRate_value = str(EURUSD_RATE)
    FXEURRate = SubElement(AIFBaseCurrencyDescription, 'FXEURRate')
    FXEURRate.text = FXEURRate_value
    table_from_base_cncy.append(['51', 'FX EUR Rate', FXEURRate_value])

    AIFNetAssetValue_value = str(NAV_USD)
    AIFNetAssetValue = SubElement(AIFDescription, 'AIFNetAssetValue')
    AIFNetAssetValue.text = AIFNetAssetValue_value
    table_from_base_cncy.append(['53', 'AIF Net Asset Value', AIFNetAssetValue_value])

    PredominantAIFType_value = ['HFND', 'Hedge Fund']
    PredominantAIFType = SubElement(AIFDescription, 'PredominantAIFType')
    PredominantAIFType.text = PredominantAIFType_value[0]
    table_from_base_cncy.append(['57', 'Predominant AIF Type', f'{PredominantAIFType_value[0]}: {PredominantAIFType_value[1]}'])

    HedgeFundInvestmentStrategies = SubElement(AIFDescription, 'HedgeFundInvestmentStrategies')
    HedgeFundStrategy = SubElement(HedgeFundInvestmentStrategies, 'HedgeFundStrategy')

    HedgeFundStrategyType_value = Investment_strategy[0]
    HedgeFundStrategyType = SubElement(HedgeFundStrategy, 'HedgeFundStrategyType')
    HedgeFundStrategyType.text = HedgeFundStrategyType_value
    table_from_base_cncy.append(['58', 'Hedge Fund Strategy Type', f'{Investment_strategy[0]}: {Investment_strategy[1]}'])

    PrimarystrategyFlag_value = 'true'
    PrimarystrategyFlag = SubElement(HedgeFundStrategy, 'PrimarystrategyFlag')
    PrimarystrategyFlag.text = PrimarystrategyFlag_value
    table_from_base_cncy.append(['59', 'Primary strategy Flag', PrimarystrategyFlag_value])

    StrategyNAVRate_value = '100'
    StrategyNAVRate = SubElement(HedgeFundStrategy, 'StrategyNAVRate')
    StrategyNAVRate.text = StrategyNAVRate_value
    table_from_base_cncy.append(['60', 'Strategy NAV Rate', str(StrategyNAVRate_value)])

    html += list_to_html_table(table_from_base_cncy, 'Base Cncy + Strategy (N48-63)')

    my_sql = f"""SELECT T2.ticker,T2.isin,T2.name,macro_code,macro_label,asset_label,asset_code,subasset_label,
                    subasset_code,round(abs(mkt_value_usd),0) as notional_usd,
                    if(mkt_value_usd>0,'L','S') as side,T2.prod_type,T2.mic,T4.continent FROM anandaprod.position T1 
                    JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                    JOIN country T4 on T3.country_id=T4.id JOIN aifmd T5 on T5.id=T2.aifmd_exposure_id
                    WHERE T1.entry_date='{end_date}' and parent_fund_id={fund_id} order by abs(mkt_value_usd) desc"""
    df = pd.read_sql(my_sql, con=engine)
    total_usd = df['notional_usd'].sum()

    # 5 Biggest AIFM Assets
    table_main_instruments = [['Rank', 'sub-asset', 'code type', 'Instrument Name', 'ISIN', 'Position Type', 'Position Value']]
    MainInstrumentsTraded = SubElement(AIFPrincipalInfo, 'MainInstrumentsTraded')

    df_big_asset = df[:5]

    for index, row in df_big_asset.iterrows():
        ticker = row['ticker']
        prod_type = row['prod_type']
        isin = row['isin']
        side = row['side']
        notional_usd = row['notional_usd']
        InstrumentName_value = row['name']
        if prod_type == 'Future':
            fut_product = find_active_contract(ticker, end_date)
            if fut_product.isin:
                isin = fut_product.isin
            InstrumentName_value = fut_product.name
        MainInstrumentTraded = SubElement(MainInstrumentsTraded, 'MainInstrumentTraded')

        Ranking_value = str(index+1)
        Ranking = SubElement(MainInstrumentTraded, 'Ranking')
        Ranking.text = Ranking_value

        SubAssetType_value = row['subasset_code']
        SubAssetType_label = row['subasset_label']
        SubAssetType = SubElement(MainInstrumentTraded, 'SubAssetType')
        SubAssetType.text = SubAssetType_value

        if isin:
            InstrumentCodeType_value = 'ISIN'
        else:
            InstrumentCodeType_value = 'NONE'
        InstrumentCodeType = SubElement(MainInstrumentTraded, 'InstrumentCodeType')
        InstrumentCodeType.text = InstrumentCodeType_value

        InstrumentName = SubElement(MainInstrumentTraded, 'InstrumentName')
        InstrumentName.text = InstrumentName_value

        if isin:
            ISINInstrumentIdentification = SubElement(MainInstrumentTraded, 'ISINInstrumentIdentification')
            ISINInstrumentIdentification.text = isin

        PositionType_value = side

        PositionType = SubElement(MainInstrumentTraded, 'PositionType')
        PositionType.text = PositionType_value

        PositionValue_value = str(int(notional_usd))
        PositionValue = SubElement(MainInstrumentTraded, 'PositionValue')
        PositionValue.text = PositionValue_value

        table_main_instruments.append([Ranking_value, f'{SubAssetType_value}: {SubAssetType_label}',
                                       InstrumentCodeType_value, InstrumentName_value, isin,
                                       PositionType_value, PositionValue_value])

    html += list_to_html_table(table_main_instruments, 'Main Instruments (N64-77)')

    # Geographical Focus
    table_geo_focus = [['Continent', 'NAV(%)', "AUM(%)"]]
    NAVGeographicalFocus = SubElement(AIFPrincipalInfo, 'NAVGeographicalFocus')

    my_sql = f"""SELECT continent,abs(sum(mkt_value_usd)) as aggr_value FROM anandaprod.position T1 
                 JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                 JOIN Country T4 on T3.country_id=T4.id
                 WHERE T1.entry_date='{end_date}' and parent_fund_id={fund_id} group by continent order by abs(sum(mkt_value_usd));"""
    df_geo = pd.read_sql(my_sql, con=engine, index_col='continent')
    total_position = df_geo['aggr_value'].sum()

    AfricaNAVRate_value = 0
    if 'APAC' in df_geo.index:
        AsiaPacificNAVRate_value = round(df_geo.loc['APAC']['aggr_value'] / total_position, 4) * 100
    else:
        AsiaPacificNAVRate_value = 0
    EuropeNAVRate_value = 0
    EEANAVRate_value = round(df_geo.loc['EMEA']['aggr_value'] / total_position, 4) * 100
    MiddleEastNAVRate_value = 0
    # NorthAmericaNAVRate_value = round(df_geo.loc['AMER']['aggr_value'] / total_position, 4) * 100
    NorthAmericaNAVRate_value = 100 - EEANAVRate_value - AsiaPacificNAVRate_value
    SouthAmericaNAVRate_value = 0
    SupraNationalNAVRate_value = 0

    AfricaNAVRate = SubElement(NAVGeographicalFocus, 'AfricaNAVRate')
    AfricaNAVRate.text = str(AfricaNAVRate_value)

    AsiaPacificNAVRate = SubElement(NAVGeographicalFocus, 'AsiaPacificNAVRate')
    AsiaPacificNAVRate.text = str(AsiaPacificNAVRate_value)

    EuropeNAVRate = SubElement(NAVGeographicalFocus, 'EuropeNAVRate')
    EuropeNAVRate.text = str(EuropeNAVRate_value)

    EEANAVRate = SubElement(NAVGeographicalFocus, 'EEANAVRate')
    EEANAVRate.text = str(EEANAVRate_value)

    MiddleEastNAVRate = SubElement(NAVGeographicalFocus, 'MiddleEastNAVRate')
    MiddleEastNAVRate.text = str(MiddleEastNAVRate_value)

    NorthAmericaNAVRate = SubElement(NAVGeographicalFocus, 'NorthAmericaNAVRate')
    NorthAmericaNAVRate.text = str(NorthAmericaNAVRate_value)

    SouthAmericaNAVRate = SubElement(NAVGeographicalFocus, 'SouthAmericaNAVRate')
    SouthAmericaNAVRate.text = str(SouthAmericaNAVRate_value)

    SupraNationalNAVRate = SubElement(NAVGeographicalFocus, 'SupraNationalNAVRate')
    SupraNationalNAVRate.text = str(SupraNationalNAVRate_value)

    #TODO: check putting NAV and AUM same % is OK - Bainbridge did that. UK should not be EEA anymore?

    AUMGeographicalFocus = SubElement(AIFPrincipalInfo, 'AUMGeographicalFocus')

    AfricaAUMRate_value = AfricaNAVRate_value
    AsiaPacificAUMRate_value = AsiaPacificNAVRate_value
    EuropeAUMRate_value = EuropeNAVRate_value
    EEAAUMRate_value = EEANAVRate_value
    MiddleEastAUMRate_value = MiddleEastNAVRate_value
    NorthAmericaAUMRate_value = NorthAmericaNAVRate_value
    SouthAmericaAUMRate_value = SouthAmericaNAVRate_value
    SupraNationalAUMRate_value = SupraNationalNAVRate_value

    AfricaAUMRate = SubElement(AUMGeographicalFocus, 'AfricaAUMRate')
    AfricaAUMRate.text = str(AfricaAUMRate_value)

    AsiaPacificAUMRate = SubElement(AUMGeographicalFocus, 'AsiaPacificAUMRate')
    AsiaPacificAUMRate.text = str(AsiaPacificAUMRate_value)

    EuropeAUMRate = SubElement(AUMGeographicalFocus, 'EuropeAUMRate')
    EuropeAUMRate.text = str(EuropeAUMRate_value)

    EEAAUMRate = SubElement(AUMGeographicalFocus, 'EEAAUMRate')
    EEAAUMRate.text = str(EEAAUMRate_value)

    MiddleEastAUMRate = SubElement(AUMGeographicalFocus, 'MiddleEastAUMRate')
    MiddleEastAUMRate.text = str(MiddleEastAUMRate_value)

    NorthAmericaAUMRate = SubElement(AUMGeographicalFocus, 'NorthAmericaAUMRate')
    NorthAmericaAUMRate.text = str(NorthAmericaAUMRate_value)

    SouthAmericaAUMRate = SubElement(AUMGeographicalFocus, 'SouthAmericaAUMRate')
    SouthAmericaAUMRate.text = str(SouthAmericaAUMRate_value)

    SupraNationalAUMRate = SubElement(AUMGeographicalFocus, 'SupraNationalAUMRate')
    SupraNationalAUMRate.text = str(SupraNationalAUMRate_value)

    table_geo_focus.append(['Africa', str(AfricaNAVRate_value), str(AfricaAUMRate_value)])
    table_geo_focus.append(['Asia Pacific', str(AsiaPacificNAVRate_value), str(AsiaPacificAUMRate_value)])
    table_geo_focus.append(['Europe', str(EuropeNAVRate_value), str(EuropeAUMRate_value)])
    table_geo_focus.append(['EEA', str(EEANAVRate_value), str(EEAAUMRate_value)])
    table_geo_focus.append(['Middle East NAV Rate', str(MiddleEastNAVRate_value), str(MiddleEastAUMRate_value)])
    table_geo_focus.append(['North America NAV Rate', str(NorthAmericaNAVRate_value), str(NorthAmericaAUMRate_value)])
    table_geo_focus.append(['South America NAV Rate', str(SouthAmericaNAVRate_value), str(SouthAmericaAUMRate_value)])
    table_geo_focus.append(['Supra National NAV Rate', str(SupraNationalNAVRate_value), str(SupraNationalAUMRate_value)])

    html += list_to_html_table(table_geo_focus, 'Geographical Breakdown (N78-93)')

    # 10 Principal Exposures (94-102)
    table_principal_exposure = [['ranking', 'Macro Type', 'Sub Asset Type', 'Position', 'Aggreg Value Amount', 'Aggreg Rate']]
    PrincipalExposures = SubElement(AIFPrincipalInfo, 'PrincipalExposures')

    df_big_assets = df.groupby(['macro_label', 'macro_code', 'subasset_label', 'subasset_code', 'side'], as_index=False)[['notional_usd']].sum()
    df_big_assets.sort_values(by='notional_usd', ascending=False, inplace=True)
    df_big_assets = df_big_assets[:10]
    df_big_assets = df_big_assets.reset_index()

    # TODO Check that taking abs value is correct. Add FX in there? Bainbridge take abs and add some FX (Like AUM)
    # TODO: check that the sum is 100, check that the sum match the AUM

    for index, row in df_big_assets.iterrows():
        macro_label = row['macro_label']
        macro_code = row['macro_code']
        subasset_label = row['subasset_label']
        subasset_code = row['subasset_code']
        notional_usd = row['notional_usd']
        side = row['side']

        PrincipalExposure = SubElement(PrincipalExposures, 'PrincipalExposure')
        Ranking_value = str(index + 1)
        Ranking = SubElement(PrincipalExposure, 'Ranking')
        Ranking.text = Ranking_value

        AssetMacroType_value = [macro_label, macro_code]
        AssetMacroType = SubElement(PrincipalExposure, 'AssetMacroType')
        AssetMacroType.text = AssetMacroType_value[1]

        SubAssetType_value = [subasset_label, subasset_code]
        SubAssetType = SubElement(PrincipalExposure, 'SubAssetType')
        SubAssetType.text = SubAssetType_value[1]

        PositionType_value = side
        PositionType = SubElement(PrincipalExposure, 'PositionType')
        PositionType.text = PositionType_value

        AggregatedValueAmount_value = str(int(notional_usd))
        AggregatedValueAmount = SubElement(PrincipalExposure, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value

        AggregatedValueRate_value = str(round(100 * notional_usd / total_usd, 2))
        AggregatedValueRate = SubElement(PrincipalExposure, 'AggregatedValueRate')
        AggregatedValueRate.text = AggregatedValueRate_value

        table_principal_exposure.append([Ranking_value, f'{AssetMacroType_value[0]}: {AssetMacroType_value[1]}',
                                        f'{SubAssetType_value[0]}: {SubAssetType_value[1]}', PositionType_value,
                                        AggregatedValueAmount_value, AggregatedValueRate_value])

    # add missing rank
    rows_num = len(df.index)
    if rows_num < 10:
        for i in range(rows_num+1, 11):
            PrincipalExposure = SubElement(PrincipalExposures, 'PrincipalExposure')
            Ranking_value = str(i)
            Ranking = SubElement(PrincipalExposure, 'Ranking')
            Ranking.text = Ranking_value

            AssetMacroType_value = 'NTA'
            AssetMacroType = SubElement(PrincipalExposure, 'AssetMacroType')
            AssetMacroType.text = AssetMacroType_value

            table_principal_exposure.append([Ranking_value, f'NTA: Missing Rank', '', '', '', ''])

    html += list_to_html_table(table_principal_exposure, '10 Principal Exposures (N94-102)')

    # MostImportantConcentration
    table_portfolio_concentration = [['Ranking', 'Asset Type', 'MIC', 'Position', 'Aggreg Value', 'Rate %']]
    MostImportantConcentration = SubElement(AIFPrincipalInfo, 'MostImportantConcentration')

    PortfolioConcentrations = SubElement(MostImportantConcentration, 'PortfolioConcentrations')

    df_concentration = df.groupby(['asset_label', 'asset_code', 'mic', 'side'], as_index=False)[['notional_usd']].sum()
    df_concentration.sort_values(by='notional_usd', ascending=False, inplace=True)
    df_concentration = df_concentration[:5]
    df_concentration = df_concentration.reset_index()


    for index, row in df_concentration.iterrows():
        mic = row['mic']
        asset_label = row['asset_label']
        asset_code = row['asset_code']
        notional_usd = row['notional_usd']
        side = row['side']

        PortfolioConcentration = SubElement(PortfolioConcentrations, 'PortfolioConcentration')
        Ranking_value = str(index + 1)
        Ranking = SubElement(PortfolioConcentration, 'Ranking')
        Ranking.text = Ranking_value

        AssetType_value = [asset_label, asset_code]
        AssetType = SubElement(PortfolioConcentration, 'AssetType')
        AssetType.text = AssetType_value[1]

        PositionType_value = side
        PositionType = SubElement(PortfolioConcentration, 'PositionType')
        PositionType.text = PositionType_value

        MarketIdentification = SubElement(PortfolioConcentration, 'MarketIdentification')
        MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
        MarketCodeType.text = 'MIC'

        MarketCode_value = mic
        MarketCode = SubElement(MarketIdentification, 'MarketCode')
        MarketCode.text = MarketCode_value

        AggregatedValueAmount_value = str(int(notional_usd))
        AggregatedValueAmount = SubElement(PortfolioConcentration, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value

        AggregatedValueRate_value = str(round(100 * notional_usd / total_usd, 2))
        AggregatedValueRate = SubElement(PortfolioConcentration, 'AggregatedValueRate')
        AggregatedValueRate.text = AggregatedValueRate_value

        table_portfolio_concentration.append([Ranking_value, f'{AssetType_value[0]}: {AssetType_value[1]}', MarketCode_value,
                                              PositionType_value, AggregatedValueAmount_value, AggregatedValueRate_value])

    html += list_to_html_table(table_portfolio_concentration, '5 Most Important Portfolio Concentrations (N103-112)')

    # Principal Markets
    # 5 biggest markets (take only listed, not OTC)
    table_top_markets = [['Rank', 'Code', 'Aggr Value']]
    AIFPrincipalMarkets = SubElement(MostImportantConcentration, 'AIFPrincipalMarkets')

    my_sql = f"""SELECT mic,abs(sum(mkt_value_usd)) as aggr_value FROM anandaprod.position T1 
                 JOIN Product T2 on T1.product_id=T2.id WHERE T1.entry_date='{end_date}' 
                 and parent_fund_id={fund_id} group by mic order by abs(sum(mkt_value_usd)) desc LIMIT 3;"""

    df_top_markets = pd.read_sql(my_sql, con=engine)

    for index, row in df_top_markets.iterrows():
        AIFPrincipalMarket = SubElement(AIFPrincipalMarkets, 'AIFPrincipalMarket')
        Ranking_value = str(index + 1)
        Ranking = SubElement(AIFPrincipalMarket, 'Ranking')
        Ranking.text = Ranking_value

        MarketIdentification = SubElement(AIFPrincipalMarket, 'MarketIdentification')
        MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
        MarketCodeType.text = 'MIC'

        MarketCode_value = row['mic']
        MarketCode = SubElement(MarketIdentification, 'MarketCode')
        MarketCode.text = MarketCode_value

        AggregatedValueAmount_value = str(int(row['aggr_value']))
        AggregatedValueAmount = SubElement(AIFPrincipalMarket, 'AggregatedValueAmount')
        AggregatedValueAmount.text = AggregatedValueAmount_value

        table_top_markets.append([Ranking_value, MarketCode_value, AggregatedValueAmount_value])
    html += list_to_html_table(table_top_markets, 'Principal Markets (N114-117)')

    # Investor Concentration:
    InvestorConcentration = SubElement(MostImportantConcentration, 'InvestorConcentration')

    MainBeneficialOwnersRate = SubElement(InvestorConcentration, 'MainBeneficialOwnersRate')
    MainBeneficialOwnersRate.text = str(MainBeneficialOwnersRate_value)

    ProfessionalInvestorConcentrationRate_value = '100'
    ProfessionalInvestorConcentrationRate = SubElement(InvestorConcentration, 'ProfessionalInvestorConcentrationRate')
    ProfessionalInvestorConcentrationRate.text = ProfessionalInvestorConcentrationRate_value

    RetailInvestorConcentrationRate_value = '0'
    RetailInvestorConcentrationRate = SubElement(InvestorConcentration, 'RetailInvestorConcentrationRate')
    RetailInvestorConcentrationRate.text = RetailInvestorConcentrationRate_value

    table_investor = [['Question', 'Value %'],
                      ['Beneficially owned percentage by top 5 beneficial owners', MainBeneficialOwnersRate_value],
                      ['Investor Concentration percentage by professional clients', ProfessionalInvestorConcentrationRate_value],
                      ['Investor Concentration percentage by retail investors', RetailInvestorConcentrationRate_value]]

    html += list_to_html_table(table_investor, 'Investors Concentration (N118-120)')

    html += f'<br/><H2>24.2 for {my_fund}<H2>'

    output = prettify(root)
    print(output)
    xml_filename = f"AIF_{my_fund}.xml"
    with open(xml_filename, "w") as f:
        f.write(output)
    simple_email(f"AIF Report {my_fund} {quarter} {year}", '', 'olivier@ananda-am.com', html, xml_filename)
