from datetime import date, datetime
from utils import previous_quarter, simple_email
from xml.etree.ElementTree import Element, SubElement, Comment, ElementTree
from utils import prettify, list_to_html_table, find_active_contract, get_asset_list, get_investor_activity
from manual_data import EURUSD_RATE, MainBeneficialOwnersRate_alto, MainBeneficialOwnersRate_neutral, \
    AnnualInvestmentReturnRate_alto, AnnualInvestmentReturnRate_neutral, GrossInvestmentReturnsRate_alto, \
    GrossInvestmentReturnsRate_neutral, NetInvestmentReturnsRate_alto, NetInvestmentReturnsRate_neutral, \
    NAVChangeRate_alto, NAVChangeRate_neutral, Subscription_alto, Subscription_neutral, Redemption_alto, \
    Redemption_neutral, StressTestsResultArticle15_alto, \
    StressTestsResultArticle15_neutral, StressTestsResultArticle16_alto, StressTestsResultArticle16_neutral

import pandas as pd
from models import engine, session, ParentFund, ParentBroker, Margin, ShareClass


security_country_list = ['United States', 'Canada', 'Switzerland']

month_by_quarter = {'Q1': ['January', 'February', 'March'],
                    'Q2': ['April', 'May', 'June'],
                    'Q3': ['July', 'August', 'September'],
                    'Q4': ['October', 'November', 'December']}

alto_fund = session.query(ParentFund).filter(ParentFund.name == 'Alto').first()
neutral_fund = session.query(ParentFund).filter(ParentFund.name == 'Neutral').first()

alto_dict = {'AIF National Code': alto_fund.fca_code,
             'AIF Name': alto_fund.legal_name,
             'Inception Date': alto_fund.inception_date.strftime("%Y-%m-%d"),
             'AIF Identifier LEI': alto_fund.lei}

neutral_dict = {'AIF National Code': neutral_fund.fca_code,
                'AIF Name': neutral_fund.legal_name,
                'Inception Date': neutral_fund.inception_date.strftime("%Y-%m-%d"),
                'AIF Identifier LEI': neutral_fund.lei}

# Share classes name and ISIN:
alto_share_classes = [[sc.name, sc.isin] for sc in session.query(ShareClass).
    filter(ShareClass.parent_fund_id == 1).all()]

neutral_share_classes = [[sc.name, sc.isin] for sc in session.query(ShareClass).
    filter(ShareClass.parent_fund_id == 3).all()]

alto_pbs = [[brok.name, brok.legal_name, brok.lei] for brok in alto_fund.brokers]
neutral_pbs = [[brok.name, brok.legal_name, brok.lei] for brok in neutral_fund.brokers]


def create_aif(my_fund):

    my_date = date.today()
    # my_date = date(2022, 4, 1)
    quarter, start_date, end_date = previous_quarter(my_date)
    month_list = month_by_quarter[quarter]

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    year = start_date.year

    gs_asset, ms_asset, ubs_asset = get_asset_list(end_date)  # pb_name, cash, stock, cfd, money_market

    all_margin = session.query(Margin).join(ParentBroker).filter(Margin.entry_date == end_date). \
        order_by(ParentBroker.name.asc()).all()
    gs_margin_list = [m for m in all_margin if m.parent_broker.name == 'GS']
    if gs_margin_list:
        gs_margin = gs_margin_list[0]
    else:
        gs_margin = Margin(account_value=0, margin_requirement=0)

    ms_margin_list = [m for m in all_margin if m.parent_broker.name == 'MS']
    if ms_margin_list:
        ms_margin = ms_margin_list[0]
    else:
        ms_margin = Margin(account_value=0, margin_requirement=0)

    ubs_margin_list = [m for m in all_margin if m.parent_broker.name == 'UBS']
    if ubs_margin_list:
        ubs_margin = ubs_margin_list[0]
    else:
        ubs_margin = Margin(account_value=0, margin_requirement=0)

    # Subscription_value, Redemption_value = get_investor_activity(my_fund, start_date, end_date)

    if my_fund == 'ALTO':
        LastReportingFlag_value = 'false'
        aif_dict = alto_dict
        share_classes = alto_share_classes
        pbs = alto_pbs
        fund_id_list = '(1,5)'
        MainBeneficialOwnersRate_value = str(MainBeneficialOwnersRate_alto)
        AnnualInvestmentReturnRate_value = str(AnnualInvestmentReturnRate_alto)
        AllCounterpartyCollateralCash_value = str(int(gs_asset[1] + ms_asset[1] + gs_asset[2] + ms_asset[2]))  # pb_name, cash, stock, cfd, money_market
        UnencumberedCash_value = str(int(gs_margin.account_value - gs_margin.margin_requirement + ms_margin.account_value - ms_margin.margin_requirement + gs_asset[4]))
        GrossInvestmentReturnsRate_value = GrossInvestmentReturnsRate_alto
        NetInvestmentReturnsRate_value = NetInvestmentReturnsRate_alto
        NAVChangeRate_value = NAVChangeRate_alto
        Subscription_value = Subscription_alto
        Redemption_value = Redemption_alto
        StressTestsResultArticle15_value = StressTestsResultArticle15_alto
        StressTestsResultArticle16_value = StressTestsResultArticle16_alto

        Investment_strategy = ['EQTY_LGBS', 'Equity: Long Bias']
    elif my_fund == 'NEUTRAL':
        LastReportingFlag_value = 'true'
        aif_dict = neutral_dict
        share_classes = neutral_share_classes
        pbs = neutral_pbs
        fund_id_list = '(3)'
        MainBeneficialOwnersRate_value = str(MainBeneficialOwnersRate_neutral)
        AnnualInvestmentReturnRate_value = str(AnnualInvestmentReturnRate_neutral)
        AllCounterpartyCollateralCash_value = str(int(ubs_asset[1] + ubs_asset[2]))  # pb_name, cash, stock, cfd, money_market
        UnencumberedCash_value = str(int(ubs_margin.account_value - ubs_margin.margin_requirement))
        Investment_strategy = ['EQTY_LGBS', 'Equity: Long Bias']
        GrossInvestmentReturnsRate_value = GrossInvestmentReturnsRate_neutral
        NetInvestmentReturnsRate_value = NetInvestmentReturnsRate_neutral
        NAVChangeRate_value = NAVChangeRate_neutral
        Subscription_value = Subscription_neutral
        Redemption_value = Redemption_neutral
        StressTestsResultArticle15_value = StressTestsResultArticle15_neutral
        StressTestsResultArticle16_value = StressTestsResultArticle16_neutral


    my_sql = f"""SELECT T2.ticker,if(T2.isin is Null,'NA',T2.isin) as isin,T2.name,macro_code,macro_label,asset_label,asset_code,subasset_label,
                    subasset_code,round(abs(mkt_value_usd),0) as notional_usd, if(mkt_value_usd>=0,'L','S') as side,T2.prod_type,T2.mic,
                    T4.continent,T4.name as country FROM position T1 
                    JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                    JOIN country T4 on T3.country_id=T4.id JOIN aifmd T5 on T5.id=T2.aifmd_exposure_id
                    WHERE T1.entry_date='{end_date}' and parent_fund_id in {fund_id_list} order by round(abs(mkt_value_usd),0) desc"""

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

    df_aggr.to_excel(fr'H:\Compliance\AIFMD\KEY FILES\Historic\All Positions AIF {my_fund} {end_date_str}.xlsx')

    total_usd = df_aggr['notional_usd'].sum()
    AUM_USD = int(total_usd)

    tree = ElementTree("tree")

    root = Element('AIFReportingInfo', {'CreationDateAndTime': f'{now_str}',
                                         'Version': '2.0',
                                         'ReportingMemberState': 'GB',
                                         'xsi:noNamespaceSchemaLocation': 'AIFMD_DATMAN_V1.2.xsd',
                                         'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})

    comment = Comment(f'AIF Report {my_fund}')
    root.append(comment)
    table_main = [['N', 'Description', 'Value']]
    html = f'<H1><u>24.1 for {my_fund}</u><H2>'
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

    LastReportingFlag = SubElement(AIFRecordInfo, 'LastReportingFlag')
    LastReportingFlag.text = LastReportingFlag_value
    table_main.append(['13', 'Last Reporting Flag', LastReportingFlag_value])

    # Following Q&A Suggestion, I am adding assumption to explain why AUM=0
    if my_fund == 'NEUTRAL' and AUM_USD == 0:
        Assumptions = SubElement(AIFRecordInfo, 'Assumptions')
        Assumption = SubElement(Assumptions, 'Assumption')
        FCAFieldReference = SubElement(Assumption, 'FCAFieldReference')
        FCAFieldReference.text = "48"
        AssumptionDetails = SubElement(Assumption, 'AssumptionDetails')
        AssumptionDetails.text = "AIF has been liquidated"

    AIFMNationalCode_value = '924813'
    AIFMNationalCode = SubElement(AIFRecordInfo, 'AIFMNationalCode')
    AIFMNationalCode.text = AIFMNationalCode_value
    table_main.append(['16', 'AIFM National Code', AIFMNationalCode_value])

    AIFNationalCode_value = aif_dict['AIF National Code']
    AIFNationalCode = SubElement(AIFRecordInfo, 'AIFNationalCode')
    AIFNationalCode.text = AIFNationalCode_value
    table_main.append(['17', 'AIF National Code', AIFNationalCode_value])

    AIFName_value = aif_dict['AIF Name']
    AIFName = SubElement(AIFRecordInfo, 'AIFName')
    AIFName.text = AIFName_value
    table_main.append(['18', 'Name', AIFName_value])

    # AIFEEAFlag_value = 'false'
    # AIFEEAFlag = SubElement(AIFRecordInfo, 'AIFEEAFlag')
    # AIFEEAFlag.text = AIFEEAFlag_value
    # table_main.append(['19', 'AIF EEA Flag', AIFEEAFlag_value])

    # https://www.esma.europa.eu/document/tables-8-9-10-annex-2-esma-guidelines-aifmd-reporting-obligation-revised
    # Annex II - Table 9.
    AIFReportingCode_value = ['33', 'Unleveraged non EU AIF (of an AIFM with quarterly obligation) marketed in the Union']
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
    ShareClassIdentification = SubElement(AIFPrincipalInfo, 'ShareClassIdentification')

    for share_class in share_classes:
        ShareClassIdentifier = SubElement(ShareClassIdentification, 'ShareClassIdentifier')
        ShareClassNationalCode_name = share_class[0]
        ShareClassNationalCode = SubElement(ShareClassIdentifier, 'ShareClassNationalCode')
        ShareClassNationalCode.text = ShareClassNationalCode_name

        ShareClassNationalCode_isin = share_class[1]
        if ShareClassNationalCode_isin:
            ShareClassIdentifierISIN = SubElement(ShareClassIdentifier, 'ShareClassIdentifierISIN')
            ShareClassIdentifierISIN.text = ShareClassNationalCode_isin

        ShareClassName = SubElement(ShareClassIdentifier, 'ShareClassName')
        ShareClassName.text = ShareClassNationalCode_name

        table_share_class.append([ShareClassNationalCode_name, ShareClassNationalCode_isin, ShareClassNationalCode_name])

    html += list_to_html_table(table_share_class, 'Share Classes (N34-40)')

    AIFDescription = SubElement(AIFPrincipalInfo, 'AIFDescription')
    AIFMasterFeederStatus_value ='NONE'
    AIFMasterFeederStatus = SubElement(AIFDescription, 'AIFMasterFeederStatus')
    AIFMasterFeederStatus.text = AIFMasterFeederStatus_value

    html += f"<H4>41) AIF Master Feeder Status : {AIFMasterFeederStatus_value}</H4>"

    PrimeBrokers = SubElement(AIFDescription, 'PrimeBrokers')

    table_pb = [['Entity Name', 'LEI']]
    for pb in pbs:
        PrimeBrokerIdentification = SubElement(PrimeBrokers, 'PrimeBrokerIdentification')

        EntityName_value = pb[1]
        EntityName = SubElement(PrimeBrokerIdentification, 'EntityName')
        EntityName.text = EntityName_value

        EntityIdentificationLEI_value = pb[2]
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

    # NAV for AIF
    # AIFNetAssetValue_value = str(NAV_USD)
    my_sql = f"""SELECT round(sum(mkt_value_usd),0) as nav FROM position WHERE entry_date='{end_date}' and parent_fund_id in {fund_id_list}"""
    df_nav = pd.read_sql(my_sql, con=engine)
    NAV_USD = int(df_nav['nav'].sum())
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

    TotalOpenPositions_value = len(df_aggr.index)

    # 5 Main Instruments
    table_main_instruments = [['Rank', 'sub-asset', 'code type', 'Instrument Name', 'ISIN', 'AII',
                               'Position Type', 'Position Value']]
    MainInstrumentsTraded = SubElement(AIFPrincipalInfo, 'MainInstrumentsTraded')

    df_main_instrument = df_aggr.groupby(['macro_label', 'macro_code', 'subasset_label', 'subasset_code',
                                          'side', 'ticker', 'prod_type', 'isin', 'name'], as_index=False)[
        ['notional_usd']].sum()

    if not df_main_instrument.empty:
        df_main_instrument.sort_values(by='notional_usd', ascending=False, inplace=True)
        df_main_instrument = df_main_instrument[:5]
        df_main_instrument = df_main_instrument.reset_index()

        for index, row in df_main_instrument.iterrows():
            ticker = row['ticker']
            prod_type = row['prod_type']
            isin = row['isin']
            aii = ''
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

            if isin != 'NA':
                InstrumentCodeType_value = 'ISIN'
            else:
                InstrumentCodeType_value = 'AII'
            InstrumentCodeType = SubElement(MainInstrumentTraded, 'InstrumentCodeType')
            InstrumentCodeType.text = InstrumentCodeType_value

            InstrumentName = SubElement(MainInstrumentTraded, 'InstrumentName')
            InstrumentName.text = InstrumentName_value

            if isin != 'NA':
                ISINInstrumentIdentification = SubElement(MainInstrumentTraded, 'ISINInstrumentIdentification')
                ISINInstrumentIdentification.text = isin
            else:
                if fut_product:
                    AIIExchangeCode_value = fut_product.mic
                    AIIProductCode_value = fut_product.name.split(" ")[0]
                    AIIDerivativeType_value = "F"
                    AIIPutCallIdentifier_value = "F"
                    AIIExpiryDate_value = str(fut_product.expiry)
                    AIIStrikePrice_value = "0"
                    aii = f"""{AIIExchangeCode_value} {AIIProductCode_value} {AIIDerivativeType_value} 
                               {AIIPutCallIdentifier_value} {AIIExpiryDate_value} {AIIStrikePrice_value}"""

                AIIInstrumentIdentification = SubElement(MainInstrumentTraded, 'AIIInstrumentIdentification')
                AIIExchangeCode = SubElement(AIIInstrumentIdentification, 'AIIExchangeCode')
                AIIExchangeCode.text = AIIExchangeCode_value

                AIIProductCode = SubElement(AIIInstrumentIdentification, 'AIIProductCode')
                AIIProductCode.text = AIIProductCode_value

                AIIDerivativeType = SubElement(AIIInstrumentIdentification, 'AIIDerivativeType')
                AIIDerivativeType.text = AIIDerivativeType_value

                AIIPutCallIdentifier = SubElement(AIIInstrumentIdentification, 'AIIPutCallIdentifier')
                AIIPutCallIdentifier.text = AIIPutCallIdentifier_value

                AIIExpiryDate = SubElement(AIIInstrumentIdentification, 'AIIExpiryDate')
                AIIExpiryDate.text = AIIExpiryDate_value

                AIIStrikePrice = SubElement(AIIInstrumentIdentification, 'AIIStrikePrice')
                AIIStrikePrice.text = AIIStrikePrice_value

            PositionType_value = side

            PositionType = SubElement(MainInstrumentTraded, 'PositionType')
            PositionType.text = PositionType_value

            PositionValue_value = str(int(notional_usd))
            PositionValue = SubElement(MainInstrumentTraded, 'PositionValue')
            PositionValue.text = PositionValue_value

            table_main_instruments.append([Ranking_value, f'{SubAssetType_value}: {SubAssetType_label}',
                                           InstrumentCodeType_value, InstrumentName_value, isin, aii,
                                           PositionType_value, PositionValue_value])

    # add missing rank
    rows_num = len(df_main_instrument.index)
    if rows_num < 5:
        for i in range(rows_num+1, 6):
            MainInstrumentTraded = SubElement(MainInstrumentsTraded, 'MainInstrumentTraded')

            Ranking_value = str(i)
            Ranking = SubElement(MainInstrumentTraded, 'Ranking')
            Ranking.text = Ranking_value

            SubAssetType_value = 'NTA_NTA_NOTA'
            SubAssetType_label = 'Non Applicable'
            SubAssetType = SubElement(MainInstrumentTraded, 'SubAssetType')
            SubAssetType.text = SubAssetType_value

            table_main_instruments.append([Ranking_value, f'{SubAssetType_value}: {SubAssetType_label}',
                                           '', '', '', '', '', ''])

    html += list_to_html_table(table_main_instruments, 'Main Instruments (N64-77)')

    # Geographical Focus: NAV can be<0, UK out of EEA
    table_geo_focus = [['Continent', 'NAV(%)', "AUM(%)"]]
    NAVGeographicalFocus = SubElement(AIFPrincipalInfo, 'NAVGeographicalFocus')

    my_sql = f"""SELECT T4.name as country,continent,sum(mkt_value_usd) as aggr_value FROM position T1 
                 JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                 JOIN Country T4 on T3.country_id=T4.id
                 WHERE T1.entry_date='{end_date}' and parent_fund_id in {fund_id_list} group by continent,T4.name order by sum(mkt_value_usd);"""
    df_geo = pd.read_sql(my_sql, con=engine)
    total_position = df_geo['aggr_value'].sum()
    AsiaNAVPosition = df_geo.loc[df_geo['continent'] == 'APAC', 'aggr_value'].sum()
    UKNAVPosition = df_geo.loc[df_geo['country'] == 'United Kingdom', 'aggr_value'].sum()
    EuropeNonUKNAVPosition = df_geo.loc[(df_geo['continent'] == 'EMEA') &
                                        (df_geo['country'] != 'United Kingdom'), 'aggr_value'].sum()
    NorthAmericaNAVPosition = df_geo.loc[df_geo['continent'] == 'AMER', 'aggr_value'].sum()

    if total_position == 0:
        AfricaNAVRate_value = 0
        AsiaPacificNAVRate_value = 0
        UKNAVRate_value = 0
        EuropeNonUKNAVRate_value = 0
        MiddleEastNAVRate_value = 0
        NorthAmericaNAVRate_value = 100
        SouthAmericaNAVRate_value = 0
        SupraNationalNAVRate_value = 0
    else:
        AfricaNAVRate_value = 0
        if 'APAC' in df_geo.index:
            AsiaPacificNAVRate_value = round(round(AsiaNAVPosition / total_position, 4) * 100, 2)
        else:
            AsiaPacificNAVRate_value = 0

        UKNAVRate_value = round(round(UKNAVPosition / total_position, 4) * 100, 2)
        EuropeNonUKNAVRate_value = round(round(EuropeNonUKNAVPosition / total_position, 4) * 100, 2)
        MiddleEastNAVRate_value = 0
        # NorthAmericaNAVRate_value = round(NorthAmericaNAVPosition / total_position, 4) * 100
        NorthAmericaNAVRate_value = round(100 - UKNAVRate_value - EuropeNonUKNAVRate_value - AsiaPacificNAVRate_value, 2)
        SouthAmericaNAVRate_value = 0
        SupraNationalNAVRate_value = 0

    AfricaNAVRate = SubElement(NAVGeographicalFocus, 'AfricaNAVRate')
    AfricaNAVRate.text = str(AfricaNAVRate_value)

    AsiaPacificNAVRate = SubElement(NAVGeographicalFocus, 'AsiaPacificNAVRate')
    AsiaPacificNAVRate.text = str(AsiaPacificNAVRate_value)

    UKNAVRate = SubElement(NAVGeographicalFocus, 'UKNAVRate')
    UKNAVRate.text = str(UKNAVRate_value)

    EuropeNonUKNAVRate = SubElement(NAVGeographicalFocus, 'EuropeNonUKNAVRate')
    EuropeNonUKNAVRate.text = str(EuropeNonUKNAVRate_value)

    MiddleEastNAVRate = SubElement(NAVGeographicalFocus, 'MiddleEastNAVRate')
    MiddleEastNAVRate.text = str(MiddleEastNAVRate_value)

    NorthAmericaNAVRate = SubElement(NAVGeographicalFocus, 'NorthAmericaNAVRate')
    NorthAmericaNAVRate.text = str(NorthAmericaNAVRate_value)

    SouthAmericaNAVRate = SubElement(NAVGeographicalFocus, 'SouthAmericaNAVRate')
    SouthAmericaNAVRate.text = str(SouthAmericaNAVRate_value)

    SupraNationalNAVRate = SubElement(NAVGeographicalFocus, 'SupraNationalNAVRate')
    SupraNationalNAVRate.text = str(SupraNationalNAVRate_value)

    my_sql = f"""SELECT T4.name as country,continent,sum(abs(mkt_value_usd)) as aggr_value FROM position T1 
                 JOIN Product T2 on T1.product_id=T2.id JOIN exchange T3 on T2.exchange_id=T3.id
                 JOIN Country T4 on T3.country_id=T4.id
                 WHERE T1.entry_date='{end_date}' and parent_fund_id in {fund_id_list} group by continent,T4.name order by sum(abs(mkt_value_usd));"""
    df_geo = pd.read_sql(my_sql, con=engine, )
    total_position = df_geo['aggr_value'].sum()
    AsiaAUMPosition = df_geo.loc[df_geo['continent'] == 'APAC', 'aggr_value'].sum()
    UKAUMPosition = df_geo.loc[df_geo['country'] == 'United Kingdom', 'aggr_value'].sum()
    EuropeNonUKAUMPosition = df_geo.loc[(df_geo['continent'] == 'EMEA') &
                                        (df_geo['country'] != 'United Kingdom'), 'aggr_value'].sum()
    NorthAmericaAUMPosition = df_geo.loc[df_geo['continent'] == 'AMER', 'aggr_value'].sum()

    if total_position == 0:
        AfricaAUMRate_value = 0
        AsiaPacificAUMRate_value = 0
        UKAUMRate_value = 0
        EuropeNonUKAUMRate_value = 0
        MiddleEastAUMRate_value = 0
        NorthAmericaAUMRate_value = 100
        SouthAmericaAUMRate_value = 0
        SupraNationalAUMRate_value = 0
    else:
        AfricaAUMRate_value = 0
        if 'APAC' in df_geo.index:
            AsiaPacificAUMRate_value = round(round(AsiaAUMPosition / total_position, 4) * 100, 2)
        else:
            AsiaPacificAUMRate_value = 0
        UKAUMRate_value = round(round(UKAUMPosition / total_position, 4) * 100, 2)
        EuropeNonUKAUMRate_value = round(round(EuropeNonUKAUMPosition / total_position, 4) * 100, 2)
        MiddleEastAUMRate_value = 0
        # NorthAmericaAUMRate_value = round(NorthAmericaAUMPosition / total_position, 4) * 100
        NorthAmericaAUMRate_value = round(100 - UKAUMRate_value - EuropeNonUKAUMRate_value - AsiaPacificAUMRate_value, 2)
        SouthAmericaAUMRate_value = 0
        SupraNationalAUMRate_value = 0

    AUMGeographicalFocus = SubElement(AIFPrincipalInfo, 'AUMGeographicalFocus')

    AfricaAUMRate = SubElement(AUMGeographicalFocus, 'AfricaAUMRate')
    AfricaAUMRate.text = str(AfricaAUMRate_value)

    AsiaPacificAUMRate = SubElement(AUMGeographicalFocus, 'AsiaPacificAUMRate')
    AsiaPacificAUMRate.text = str(AsiaPacificAUMRate_value)

    UKAUMRate = SubElement(AUMGeographicalFocus, 'UKAUMRate')
    UKAUMRate.text = str(UKAUMRate_value)

    EuropeNonUKAUMRate = SubElement(AUMGeographicalFocus, 'EuropeNonUKAUMRate')
    EuropeNonUKAUMRate.text = str(EuropeNonUKAUMRate_value)

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
    table_geo_focus.append(['UK', str(UKNAVRate_value), str(UKAUMRate_value)])
    table_geo_focus.append(['Europe', str(EuropeNonUKNAVRate_value), str(EuropeNonUKAUMRate_value)])
    table_geo_focus.append(['Middle East', str(MiddleEastNAVRate_value), str(MiddleEastAUMRate_value)])
    table_geo_focus.append(['North America', str(NorthAmericaNAVRate_value), str(NorthAmericaAUMRate_value)])
    table_geo_focus.append(['South America', str(SouthAmericaNAVRate_value), str(SouthAmericaAUMRate_value)])
    table_geo_focus.append(['Supra National', str(SupraNationalNAVRate_value), str(SupraNationalAUMRate_value)])

    html += list_to_html_table(table_geo_focus, 'Geographical Breakdown (N78-93)')

    # 10 Principal Exposures (94-102)
    # FCA Guidelines: Listed equities: Do not include in this category exposures obtained synthetically or through derivatives
    # (instead include these under the ‘equity derivatives’ category).
    table_principal_exposure = [['ranking', 'Macro Type', 'Sub Asset Type', 'Position', 'Aggreg Value Amount', 'Aggreg Rate']]
    PrincipalExposures = SubElement(AIFPrincipalInfo, 'PrincipalExposures')

    df_big_assets = df_aggr.groupby(['macro_label', 'macro_code', 'subasset_label', 'subasset_code', 'side'], as_index=False)[['notional_usd']].sum()

    if len(df_big_assets.index) > 0:
        df_big_assets.sort_values(by='notional_usd', ascending=False, inplace=True)
        df_big_assets = df_big_assets[:10]
        df_big_assets = df_big_assets.reset_index()

        df_big_assets['perc'] = round(100*df_big_assets['notional_usd'] / total_usd, 2)

        perc_total = df_big_assets['perc'].sum()

        if 100.1 > perc_total > 99.9:
            adjust_perc = round(100 - perc_total, 2)
            df_big_assets.at[0, 'perc'] = round(df_big_assets.iloc[0]['perc'] + adjust_perc, 2)

        for index, row in df_big_assets.iterrows():
            macro_label = row['macro_label']
            macro_code = row['macro_code']
            subasset_label = row['subasset_label']
            subasset_code = row['subasset_code']
            notional_usd = row['notional_usd']
            perc = row['perc']
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

            AggregatedValueRate_value = str(perc)
            AggregatedValueRate = SubElement(PrincipalExposure, 'AggregatedValueRate')
            AggregatedValueRate.text = AggregatedValueRate_value

            table_principal_exposure.append([Ranking_value, f'{AssetMacroType_value[0]}: {AssetMacroType_value[1]}',
                                            f'{SubAssetType_value[0]}: {SubAssetType_value[1]}', PositionType_value,
                                            AggregatedValueAmount_value, AggregatedValueRate_value])

    # add missing rank
    rows_num = len(df_big_assets.index)
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

    df_concentration = df_aggr.groupby(['asset_label', 'asset_code', 'mic', 'side'], as_index=False)[['notional_usd']].sum()
    if not df_concentration.empty:
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

            if mic == 'XXXX':
                MarketCodeType_value = 'OTC'
                MarketCodeType.text = MarketCodeType_value
                MarketCode_value = 'NA'
            else:
                MarketCodeType_value = 'MIC'
                MarketCodeType.text = MarketCodeType_value
                MarketCode_value = mic
                MarketCode = SubElement(MarketIdentification, 'MarketCode')
                MarketCode.text = MarketCode_value

            AggregatedValueAmount_value = str(int(notional_usd))
            AggregatedValueAmount = SubElement(PortfolioConcentration, 'AggregatedValueAmount')
            AggregatedValueAmount.text = AggregatedValueAmount_value

            AggregatedValueRate_value = str(round(100 * notional_usd / total_usd, 2))
            AggregatedValueRate = SubElement(PortfolioConcentration, 'AggregatedValueRate')
            AggregatedValueRate.text = AggregatedValueRate_value

            table_portfolio_concentration.append([Ranking_value, f'{AssetType_value[0]}: {AssetType_value[1]}', f'{MarketCodeType_value} - {MarketCode_value}',
                                                  PositionType_value, AggregatedValueAmount_value, AggregatedValueRate_value])

    # add missing rank
    rows_num = len(df_concentration.index)
    if rows_num < 5:
        for i in range(rows_num + 1, 6):
            PortfolioConcentration = SubElement(PortfolioConcentrations, 'PortfolioConcentration')
            Ranking_value = str(i)
            Ranking = SubElement(PortfolioConcentration, 'Ranking')
            Ranking.text = Ranking_value

            AssetType_value = 'NTA_NTA'
            AssetType = SubElement(PortfolioConcentration, 'AssetType')
            AssetType.text = AssetType_value

            table_portfolio_concentration.append([Ranking_value, f'NTA: Missing Rank', '', '', '', ''])

    html += list_to_html_table(table_portfolio_concentration, '5 Most Important Portfolio Concentrations (N103-112)')

    # Principal Markets
    # 3 biggest markets (take only listed, not OTC)
    table_top_markets = [['Rank', 'Code', 'Aggr Value']]
    AIFPrincipalMarkets = SubElement(MostImportantConcentration, 'AIFPrincipalMarkets')

    df_top_markets = df_aggr.groupby(['mic'], as_index=False)[['notional_usd']].sum()
    if not df_top_markets.empty:
        df_top_markets.sort_values(by='notional_usd', ascending=False, inplace=True)
        df_top_markets = df_top_markets[:3]
        df_top_markets = df_top_markets.reset_index()

        for index, row in df_top_markets.iterrows():
            mic = row['mic']
            AIFPrincipalMarket = SubElement(AIFPrincipalMarkets, 'AIFPrincipalMarket')
            Ranking_value = str(index + 1)
            Ranking = SubElement(AIFPrincipalMarket, 'Ranking')
            Ranking.text = Ranking_value

            MarketIdentification = SubElement(AIFPrincipalMarket, 'MarketIdentification')
            MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')

            if mic == 'XXXX':
                MarketCodeType_value = 'OTC'
                MarketCodeType.text = MarketCodeType_value
                MarketCode_value = 'NA'
            else:
                MarketCodeType_value = 'MIC'
                MarketCodeType.text = MarketCodeType_value
                MarketCode_value = mic
                MarketCode = SubElement(MarketIdentification, 'MarketCode')
                MarketCode.text = MarketCode_value

            AggregatedValueAmount_value = str(int(row['notional_usd']))
            AggregatedValueAmount = SubElement(AIFPrincipalMarket, 'AggregatedValueAmount')
            AggregatedValueAmount.text = AggregatedValueAmount_value

            table_top_markets.append([Ranking_value, f'{MarketCodeType_value} - {MarketCode_value}', AggregatedValueAmount_value])

    # add missing rank
    rows_num = len(df_top_markets)
    if rows_num < 3:
        for i in range(rows_num + 1, 4):
            AIFPrincipalMarket = SubElement(AIFPrincipalMarkets, 'AIFPrincipalMarket')
            Ranking_value = str(i)
            Ranking = SubElement(AIFPrincipalMarket, 'Ranking')
            Ranking.text = Ranking_value

            MarketIdentification = SubElement(AIFPrincipalMarket, 'MarketIdentification')
            MarketCodeType = SubElement(MarketIdentification, 'MarketCodeType')
            MarketCodeType.text = 'NOT'

            table_top_markets.append([Ranking_value, f'NOT: Missing Rank', ''])

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

    # 24.2
    html += f'<br/><H1><u>24.2 for {my_fund}</u><H1>'
    AIFIndividualInfo = SubElement(AIFCompleteDescription, 'AIFIndividualInfo')
    IndividualExposure = SubElement(AIFIndividualInfo, 'IndividualExposure')
    AssetTypeExposures = SubElement(IndividualExposure, 'AssetTypeExposures')

    table_asset_type = [['SubAsset Description', 'SubAsset Code', 'Long', 'Short']]

    df_asset_expo = df_aggr.groupby(['subasset_label', 'subasset_code', 'side'], as_index=False)[['notional_usd']].sum()
    if not df_asset_expo.empty:
        df_asset_expo.sort_values(by='notional_usd', ascending=False, inplace=True)

        df_asset_expo_long = df_asset_expo[df_asset_expo['side'] == 'L']
        df_asset_expo_long = df_asset_expo_long.rename(columns={'notional_usd': 'Long'})
        df_asset_expo_long.drop(columns=['side'], inplace=True)

        df_asset_expo_short = df_asset_expo[df_asset_expo['side'] == 'S']
        df_asset_expo_short = df_asset_expo_short.rename(columns={'notional_usd': 'Short'})
        df_asset_expo_short.drop(columns=['side'], inplace=True)

        df_asset_expo = pd.merge(df_asset_expo_long, df_asset_expo_short, how='outer')
        df_asset_expo = df_asset_expo.fillna(0)
        df_asset_expo = df_asset_expo.reset_index()

        for index, row in df_asset_expo.iterrows():
            long = row['Long']
            short = row['Short']

            AssetTypeExposure = SubElement(AssetTypeExposures, 'AssetTypeExposure')

            SubAssetType_value = [row['subasset_label'], row['subasset_code']]
            SubAssetType = SubElement(AssetTypeExposure, 'SubAssetType')
            SubAssetType.text = SubAssetType_value[1]

            LongValue_value = str(int(long))
            ShortValue_value = str(int(short))
            if long > 0:
                LongValue = SubElement(AssetTypeExposure, 'LongValue')
                LongValue.text = LongValue_value
            if short > 0:
                ShortValue = SubElement(AssetTypeExposure, 'ShortValue')
                ShortValue.text = ShortValue_value

            table_asset_type.append([SubAssetType_value[0], SubAssetType_value[1],
                                     LongValue_value, ShortValue_value])

    # add one empty line when no data
    if len(df_asset_expo.index) == 0:
        AssetTypeExposure = SubElement(AssetTypeExposures, 'AssetTypeExposure')
        SubAssetType_value = ['Other listed equity', 'SEC_LEQ_OTHR']
        SubAssetType = SubElement(AssetTypeExposure, 'SubAssetType')
        SubAssetType.text = SubAssetType_value[1]
        LongValue = SubElement(AssetTypeExposure, 'LongValue')
        LongValue.text = '0'
        table_asset_type.append([SubAssetType_value[0], SubAssetType_value[1], 0, ''])

    html += list_to_html_table(table_asset_type, 'Individual Exposures (N121-124)')

    # Turnover
    # https://www.esma.europa.eu/sites/default/files/library/2015/11/2011_379.pdf
    # Please include synthetic exposures to single stocks (i.e. CFDs) in the ‘Listed Equities’ category. Other equity derivatives (i.e. single stock futures,
    # options and equity swaps) should be included at Equity Derivatives category.
    AssetTypeTurnovers = SubElement(IndividualExposure, 'AssetTypeTurnovers')
    table_turnover = [['SubAsset Description', 'SubAsset Code', 'Market Value']]

    my_sql = f"""SELECT T3.subasset_code,T3.subasset_label,round(sum(abs(T1.notional_usd)),0) as trade_usd from trade T1 JOIN product T2 on T1.product_id=T2.id
                    JOIN aifmd T3 on T2.aifmd_turnover_id = T3.id WHERE trade_date>='{start_date}' and trade_date<='{end_date}' and T2.prod_type<>'Roll' and parent_fund_id in {fund_id_list}
                    GROUP BY T3.subasset_code,T3.subasset_label order by round(sum(abs(T1.notional_usd)),0) desc;"""
    df_turn_over = pd.read_sql(my_sql, con=engine)

    for index, row in df_turn_over.iterrows():
        AssetTypeTurnover = SubElement(AssetTypeTurnovers, 'AssetTypeTurnover')

        TurnoverSubAssetType_value = [row['subasset_code'], row['subasset_label']]
        TurnoverSubAssetType = SubElement(AssetTypeTurnover, 'TurnoverSubAssetType')
        TurnoverSubAssetType.text = TurnoverSubAssetType_value[0]

        MarketValue_value = str(int(row['trade_usd']))
        MarketValue = SubElement(AssetTypeTurnover, 'MarketValue')
        MarketValue.text = MarketValue_value

        table_turnover.append([TurnoverSubAssetType_value[0], TurnoverSubAssetType_value[1], MarketValue_value])

    html += list_to_html_table(table_turnover, 'Turnover (N125-127)')

    # Currency of Exposures
    CurrencyExposures = SubElement(IndividualExposure, 'CurrencyExposures')
    table_currency = [['Cncy', 'Long', 'Short']]

    my_sql = f"""SELECT T3.code as cncy,if(quantity>0,"L","S") as side,sum(abs(mkt_value_usd)) as notional_usd FROM position T1 JOIN product T2 on T1.product_id=T2.id
                JOIN currency T3 on T2.currency_id=T3.id JOIN aifmd T4 on T2.aifmd_exposure_id=T4.id
                WHERE entry_date='{end_date}' and parent_fund_id in {fund_id_list} group by T3.code,if(quantity>0,"L","S") order by T3.code;"""

    df_cncy = pd.read_sql(my_sql, con=engine)

    df_cncy_long = df_cncy[df_cncy['side'] == 'L']
    df_cncy_long = df_cncy_long.rename(columns={'notional_usd': 'Long'})
    df_cncy_long.drop(columns=['side'], inplace=True)

    df_cncy_short = df_cncy[df_cncy['side'] == 'S']
    df_cncy_short = df_cncy_short.rename(columns={'notional_usd': 'Short'})
    df_cncy_short.drop(columns=['side'], inplace=True)

    df_cncy = pd.merge(df_cncy_long, df_cncy_short, how='outer')
    df_cncy = df_cncy.fillna(0)

    for index, row in df_cncy.iterrows():
        long = row['Long']
        short = row['Short']
        CurrencyExposure = SubElement(CurrencyExposures, 'CurrencyExposure')

        ExposureCurrency_value = row['cncy']
        ExposureCurrency = SubElement(CurrencyExposure, 'ExposureCurrency')
        ExposureCurrency.text = ExposureCurrency_value

        LongPositionValue_value = str(int(long))
        ShortPositionValue_value = str(int(short))
        if long > 0:
            LongPositionValue = SubElement(CurrencyExposure, 'LongPositionValue')
            LongPositionValue.text = LongPositionValue_value
        if short > 0:
            ShortPositionValue = SubElement(CurrencyExposure, 'ShortPositionValue')
            ShortPositionValue.text = ShortPositionValue_value

        table_currency.append([ExposureCurrency_value, LongPositionValue_value, ShortPositionValue_value])

    # add missing rank
    if len(df_cncy.index) == 0:
        CurrencyExposure = SubElement(CurrencyExposures, 'CurrencyExposure')
        ExposureCurrency = SubElement(CurrencyExposure, 'ExposureCurrency')
        ExposureCurrency.text = 'USD'
        LongPositionValue = SubElement(CurrencyExposure, 'LongPositionValue')
        LongPositionValue.text = '0'
        table_currency.append(['USD', 0, ''])

    html += list_to_html_table(table_currency, 'Currency of exposures (N128-130)')

    # RiskProfile
    table_risk_profile = [['Num', 'Description', 'Value']]
    RiskProfile = SubElement(AIFIndividualInfo, 'RiskProfile')
    MarketRiskProfile = SubElement(RiskProfile, 'MarketRiskProfile')

    AnnualInvestmentReturnRate = SubElement(MarketRiskProfile, 'AnnualInvestmentReturnRate')
    AnnualInvestmentReturnRate.text = AnnualInvestmentReturnRate_value

    table_risk_profile.append(['137', 'Annual Investment Return Rate', f'{AnnualInvestmentReturnRate_value}%'])
    # 138-147: not reported, like Bainbridge

    #148-156
    CounterpartyRiskProfile = SubElement(RiskProfile, 'CounterpartyRiskProfile')
    TradingClearingMechanism = SubElement(CounterpartyRiskProfile, 'TradingClearingMechanism')
    TradedSecurities = SubElement(TradingClearingMechanism, 'TradedSecurities')

    future_notional = int(df_aggr.loc[df_aggr['prod_type'] == 'Future', 'notional_usd'].sum())
    cfd_notional = int(df_aggr.loc[(df_aggr['prod_type'] == 'Cash') &
                                   (~df_aggr['country'].isin(security_country_list)), 'notional_usd'].sum())
    cash_equity_notional = int(df_aggr.loc[(df_aggr['prod_type'] == 'Cash') &
                               (df_aggr['country'].isin(security_country_list)), 'notional_usd'].sum())

    if AUM_USD == 0:
        RegulatedMarketRate_value_num = 0
    else:
        RegulatedMarketRate_value_num = round(100 * (future_notional+cash_equity_notional) / AUM_USD, 2)
    RegulatedMarketRate_value = str(RegulatedMarketRate_value_num)
    RegulatedMarketRate = SubElement(TradedSecurities, 'RegulatedMarketRate')
    RegulatedMarketRate.text = RegulatedMarketRate_value
    table_risk_profile.append(['148', 'market value for securities traded on regulated exchanges', RegulatedMarketRate_value])

    OTCRate_value = str(100 - RegulatedMarketRate_value_num)
    OTCRate = SubElement(TradedSecurities, 'OTCRate')
    OTCRate.text = OTCRate_value
    table_risk_profile.append(['149', 'market value for securities traded OTC', OTCRate_value])

    TradedDerivatives = SubElement(TradingClearingMechanism, 'TradedDerivatives')
    if cfd_notional + future_notional == 0:
        RegulatedMarketRate_value_num = 0
    else:
        RegulatedMarketRate_value_num = round((100 * future_notional / (cfd_notional + future_notional)), 2)
    RegulatedMarketRate_value = str(RegulatedMarketRate_value_num)
    RegulatedMarketRate = SubElement(TradedDerivatives, 'RegulatedMarketRate')
    RegulatedMarketRate.text = RegulatedMarketRate_value
    table_risk_profile.append(['150', 'trade volumes for derivatives traded on regulated exchanges', RegulatedMarketRate_value])

    OTCRate_value = str(100 - RegulatedMarketRate_value_num)
    OTCRate = SubElement(TradedDerivatives, 'OTCRate')
    OTCRate.text = OTCRate_value
    table_risk_profile.append(['151', 'trade volumes for derivatives traded on OTC', OTCRate_value])

    ClearedDerivativesRate = SubElement(TradingClearingMechanism, 'ClearedDerivativesRate')
    if cfd_notional + future_notional == 0:
        CCPRate_value_num = 0
    else:
        CCPRate_value_num = round((100 * future_notional / (cfd_notional + future_notional)), 2)
    CCPRate_value = str(CCPRate_value_num)
    CCPRate = SubElement(ClearedDerivativesRate, 'CCPRate')
    CCPRate.text = CCPRate_value
    table_risk_profile.append(['152', 'trade volumes for derivatives cleared by CCP', CCPRate_value])

    BilateralClearingRate_value = str(100 - CCPRate_value_num)
    BilateralClearingRate = SubElement(ClearedDerivativesRate, 'BilateralClearingRate')
    BilateralClearingRate.text = BilateralClearingRate_value
    table_risk_profile.append(['153', 'trade volumes for derivatives cleared bilaterally', BilateralClearingRate_value])

    AllCounterpartyCollateral = SubElement(CounterpartyRiskProfile, 'AllCounterpartyCollateral')
    AllCounterpartyCollateralCash = SubElement(AllCounterpartyCollateral, 'AllCounterpartyCollateralCash')
    AllCounterpartyCollateralCash.text = AllCounterpartyCollateralCash_value
    table_risk_profile.append(['157', 'Collateral Cash amount posted to all counterparties', AllCounterpartyCollateralCash_value])

    html += list_to_html_table(table_risk_profile, 'Risk Profile (N137-159)')

    # Top Five Counterparty Exposures
    table_cpty = [['Ranking', 'Cpty exposure Flag', 'Name Cpty', 'LEI Cpty', 'NAV %']]
    FundToCounterpartyExposures = SubElement(CounterpartyRiskProfile, 'FundToCounterpartyExposures')

    my_sql = f"""SELECT round(sum(abs(mkt_value_usd)*qty_gs/quantity),0) as GS,round(sum(abs(mkt_value_usd)*qty_ms/quantity),0) as MS,
    round(sum(abs(mkt_value_usd)*qty_ubs/quantity),0) as UBS FROM position T1 
                 WHERE T1.entry_date='{end_date}' and parent_fund_id in {fund_id_list};"""
    df_cpty = pd.read_sql(my_sql, con=engine)

    my_sql = "SELECT name,legal_name,lei FROM parent_broker;"
    df_pb = pd.read_sql(my_sql, con=engine, index_col='name')
    df_pb.at['GS', 'amount'] = df_cpty.iloc[0]['GS']
    df_pb.at['MS', 'amount'] = df_cpty.iloc[0]['MS']
    df_pb.at['UBS', 'amount'] = df_cpty.iloc[0]['UBS']
    df_pb = df_pb.fillna(0)
    df_pb = df_pb[df_pb['amount'] != 0]
    df_pb.sort_values(by='amount', ascending=False, inplace=True)

    total_cty_usd = df_pb['amount'].sum()
    count = 1
    for index, row in df_pb.iterrows():
        FundToCounterpartyExposure = SubElement(FundToCounterpartyExposures, 'FundToCounterpartyExposure')

        Ranking_value = str(count)
        count += 1
        Ranking = SubElement(FundToCounterpartyExposure, 'Ranking')
        Ranking.text = Ranking_value

        CounterpartyExposureFlag_value = 'true'
        CounterpartyExposureFlag = SubElement(FundToCounterpartyExposure, 'CounterpartyExposureFlag')
        CounterpartyExposureFlag.text = CounterpartyExposureFlag_value

        CounterpartyIdentification = SubElement(FundToCounterpartyExposure, 'CounterpartyIdentification')
        EntityName_value = row['legal_name']
        EntityName = SubElement(CounterpartyIdentification, 'EntityName')
        EntityName.text = EntityName_value

        EntityIdentificationLEI_value = row['lei']
        EntityIdentificationLEI = SubElement(CounterpartyIdentification, 'EntityIdentificationLEI')
        EntityIdentificationLEI.text = EntityIdentificationLEI_value

        CounterpartyTotalExposureRate_value = str(round(row['amount']/total_cty_usd*100, 2))
        if CounterpartyTotalExposureRate_value == 'nan':
            CounterpartyTotalExposureRate_value = '0'
        CounterpartyTotalExposureRate = SubElement(FundToCounterpartyExposure, 'CounterpartyTotalExposureRate')
        CounterpartyTotalExposureRate.text = CounterpartyTotalExposureRate_value

        table_cpty.append([Ranking_value, CounterpartyExposureFlag_value, EntityName_value, EntityIdentificationLEI_value, CounterpartyTotalExposureRate_value])

    if count < 6:
        for count in range(count, 6):
            FundToCounterpartyExposure = SubElement(FundToCounterpartyExposures, 'FundToCounterpartyExposure')
            Ranking = SubElement(FundToCounterpartyExposure, 'Ranking')
            Ranking.text = str(count)
            CounterpartyExposureFlag = SubElement(FundToCounterpartyExposure, 'CounterpartyExposureFlag')
            CounterpartyExposureFlag.text = 'false'
            table_cpty.append([count, 'false', '', '', ''])

    html += list_to_html_table(table_cpty, 'Top Five Counterparty Exposures - AIF Exposure to Cpty (N160-165)')

    table_cpty_fund_exp = [['Ranking', 'Cpty exposure Flag', 'Name Cpty', 'LEI Cpty', 'NAV %']]
    CounterpartyToFundExposures = SubElement(CounterpartyRiskProfile, 'CounterpartyToFundExposures')
    for count in range(1, 6):
        CounterpartyToFundExposure = SubElement(CounterpartyToFundExposures, 'CounterpartyToFundExposure')
        Ranking = SubElement(CounterpartyToFundExposure, 'Ranking')
        Ranking.text = str(count)
        CounterpartyExposureFlag = SubElement(CounterpartyToFundExposure, 'CounterpartyExposureFlag')
        CounterpartyExposureFlag.text = 'false'
        table_cpty_fund_exp.append([count, 'false', '', '', ''])

    html += list_to_html_table(table_cpty_fund_exp, 'Top Five Counterparty Exposures - Cpty exposure to AIF (N166-171)')

    ClearTransactionsThroughCCPFlag_value = 'false'
    ClearTransactionsThroughCCPFlag = SubElement(CounterpartyRiskProfile, 'ClearTransactionsThroughCCPFlag')
    ClearTransactionsThroughCCPFlag.text = ClearTransactionsThroughCCPFlag_value
    html += f"<H4>172 - Direct clearing flag : {ClearTransactionsThroughCCPFlag_value}  (172-177)</H4>"

    table_liquidity = [['Num', 'Description', 'Value']]

    LiquidityRiskProfile = SubElement(RiskProfile, 'LiquidityRiskProfile')
    PortfolioLiquidityProfile = SubElement(LiquidityRiskProfile, 'PortfolioLiquidityProfile')
    PortfolioLiquidityInDays0to1Rate_value = "100"
    PortfolioLiquidityInDays0to1Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays0to1Rate')
    PortfolioLiquidityInDays0to1Rate.text = PortfolioLiquidityInDays0to1Rate_value

    PortfolioLiquidityInDays2to7Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays2to7Rate')
    PortfolioLiquidityInDays2to7Rate.text = "0"
    PortfolioLiquidityInDays8to30Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays8to30Rate')
    PortfolioLiquidityInDays8to30Rate.text = "0"
    PortfolioLiquidityInDays31to90Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays31to90Rate')
    PortfolioLiquidityInDays31to90Rate.text = "0"
    PortfolioLiquidityInDays91to180Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays91to180Rate')
    PortfolioLiquidityInDays91to180Rate.text = "0"
    PortfolioLiquidityInDays181to365Rate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays181to365Rate')
    PortfolioLiquidityInDays181to365Rate.text = "0"
    PortfolioLiquidityInDays365MoreRate = SubElement(PortfolioLiquidityProfile, 'PortfolioLiquidityInDays365MoreRate')
    PortfolioLiquidityInDays365MoreRate.text = "0"

    table_liquidity.append(['178', 'Percentage of portfolio liquidity in 0 to 1 day', PortfolioLiquidityInDays0to1Rate_value])

    UnencumberedCash = SubElement(PortfolioLiquidityProfile, 'UnencumberedCash')
    UnencumberedCash.text = UnencumberedCash_value
    table_liquidity.append(['185', 'Unencumbered cash amount', UnencumberedCash_value])

    InvestorLiquidityProfile = SubElement(LiquidityRiskProfile, 'InvestorLiquidityProfile')

    InvestorLiquidityInDays0to1Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays0to1Rate')
    InvestorLiquidityInDays0to1Rate.text = '0'
    InvestorLiquidityInDays2to7Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays2to7Rate')
    InvestorLiquidityInDays2to7Rate.text = '0'

    InvestorLiquidityInDays8to30Rate_value = "100"
    InvestorLiquidityInDays8to30Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays8to30Rate')
    InvestorLiquidityInDays8to30Rate.text = InvestorLiquidityInDays8to30Rate_value
    table_liquidity.append(['188', 'Percentage of investor liquidity in 8 to 30 days', InvestorLiquidityInDays8to30Rate_value])

    InvestorLiquidityInDays31to90Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays31to90Rate')
    InvestorLiquidityInDays31to90Rate.text = '0'
    InvestorLiquidityInDays91to180Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays91to180Rate')
    InvestorLiquidityInDays91to180Rate.text = '0'
    InvestorLiquidityInDays181to365Rate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays181to365Rate')
    InvestorLiquidityInDays181to365Rate.text = '0'
    InvestorLiquidityInDays365MoreRate = SubElement(InvestorLiquidityProfile, 'InvestorLiquidityInDays365MoreRate')
    InvestorLiquidityInDays365MoreRate.text = '0'

    InvestorRedemption = SubElement(LiquidityRiskProfile, 'InvestorRedemption')

    ProvideWithdrawalRightsFlag_value = "true"
    ProvideWithdrawalRightsFlag = SubElement(InvestorRedemption, 'ProvideWithdrawalRightsFlag')
    ProvideWithdrawalRightsFlag.text = ProvideWithdrawalRightsFlag_value
    table_liquidity.append(['193', 'Withdrawal redemption rights flag', ProvideWithdrawalRightsFlag_value])

    InvestorRedemptionFrequency_value = ['M', 'Monthly']
    InvestorRedemptionFrequency = SubElement(InvestorRedemption, 'InvestorRedemptionFrequency')
    InvestorRedemptionFrequency.text = InvestorRedemptionFrequency_value[0]
    table_liquidity.append(['194', 'Investor Redemption Frequency', f'{InvestorRedemptionFrequency_value[0]}: {InvestorRedemptionFrequency_value[1]}'])

    InvestorRedemptionNoticePeriod_value = "30"
    InvestorRedemptionNoticePeriod = SubElement(InvestorRedemption, 'InvestorRedemptionNoticePeriod')
    InvestorRedemptionNoticePeriod.text = InvestorRedemptionNoticePeriod_value
    table_liquidity.append(['195', 'Investor Redemption Notice Period in days', InvestorRedemptionNoticePeriod_value])

    InvestorGroups = SubElement(LiquidityRiskProfile, 'InvestorGroups')
    InvestorGroup = SubElement(InvestorGroups, 'InvestorGroup')

    InvestorGroupType_value = ['HHLD', 'Households']
    InvestorGroupType = SubElement(InvestorGroup, 'InvestorGroupType')
    InvestorGroupType.text = InvestorGroupType_value[0]
    table_liquidity.append(['208', 'Investor Group Type', f'{InvestorGroupType_value[0]}: {InvestorGroupType_value[1]}'])

    InvestorGroupRate_value = "100"
    InvestorGroupRate = SubElement(InvestorGroup, 'InvestorGroupRate')
    InvestorGroupRate.text = InvestorGroupRate_value
    table_liquidity.append(['209', 'Investor Group Rate', InvestorGroupRate_value])
    html += list_to_html_table(table_liquidity, 'Liquidity Profile (N178-217)')

    # Financing liquidity (210-217) - Not reported
    OperationalRisk = SubElement(RiskProfile, 'OperationalRisk')
    TotalOpenPositions = SubElement(OperationalRisk, 'TotalOpenPositions')
    TotalOpenPositions.text = str(TotalOpenPositions_value)

    html += f"<H4>218) Total number of open positions : {TotalOpenPositions_value}</H4>"

    table_operation_risk = [['Field', month_list[0], month_list[1], month_list[2]]]

    HistoricalRiskProfile = SubElement(OperationalRisk, 'HistoricalRiskProfile')
    GrossInvestmentReturnsRate = SubElement(HistoricalRiskProfile, 'GrossInvestmentReturnsRate')

    for i in range(0, 3):
        RateMonth = SubElement(GrossInvestmentReturnsRate, f'Rate{month_list[i]}')
        RateMonth.text = str(GrossInvestmentReturnsRate_value[i])
    table_operation_risk.append(['Gross Investment Returns Rate', GrossInvestmentReturnsRate_value[0],
                                 GrossInvestmentReturnsRate_value[1], GrossInvestmentReturnsRate_value[2]])

    NetInvestmentReturnsRate = SubElement(HistoricalRiskProfile, 'NetInvestmentReturnsRate')
    for i in range(0, 3):
        RateMonth = SubElement(NetInvestmentReturnsRate, f'Rate{month_list[i]}')
        RateMonth.text = str(NetInvestmentReturnsRate_value[i])
    table_operation_risk.append(
        ['Net Investment Returns Rate', NetInvestmentReturnsRate_value[0], NetInvestmentReturnsRate_value[1],
         NetInvestmentReturnsRate_value[2]])

    NAVChangeRate = SubElement(HistoricalRiskProfile, 'NAVChangeRate')
    for i in range(0, 3):
        RateMonth = SubElement(NAVChangeRate, f'Rate{month_list[i]}')
        RateMonth.text = str(NAVChangeRate_value[i])
    table_operation_risk.append(
        ['NAV Change Rate', NAVChangeRate_value[0], NAVChangeRate_value[1],
         NAVChangeRate_value[2]])

    Subscription = SubElement(HistoricalRiskProfile, 'Subscription')
    for i in range(0, 3):
        QuantityMonth = SubElement(Subscription, f'Quantity{month_list[i]}')
        QuantityMonth.text = str(Subscription_value[i])
    table_operation_risk.append(
        ['Subscription', Subscription_value[0], Subscription_value[1],
         Subscription_value[2]])

    Redemption = SubElement(HistoricalRiskProfile, 'Redemption')
    for i in range(0, 3):
        QuantityMonth = SubElement(Redemption, f'Quantity{month_list[i]}')
        QuantityMonth.text = str(Redemption_value[i])
    table_operation_risk.append(
        ['Redemption', Redemption_value[0], Redemption_value[1],
         Redemption_value[2]])

    html += list_to_html_table(table_operation_risk, 'Historical Risk Profile (N219-278)')

    StressTests = SubElement(AIFIndividualInfo, 'StressTests')
    StressTestsResultArticle15 = SubElement(StressTests, 'StressTestsResultArticle15')
    StressTestsResultArticle15.text = StressTestsResultArticle15_value
    html += f"<H4>279) Results of stress tests performed in accordance with point(b) of Article 15(3) : {StressTestsResultArticle15_value}</H4>"

    StressTestsResultArticle16 = SubElement(StressTests, 'StressTestsResultArticle16')
    StressTestsResultArticle16.text = StressTestsResultArticle16_value
    html += f"<H4>280) Results of stress tests performed in accordance with the second subparagraph of Article 16(1) : {StressTestsResultArticle16_value}</H4>"

    AIFLeverageInfo = SubElement(AIFCompleteDescription, 'AIFLeverageInfo')
    table_leverage = [['Num', 'Field', 'Value']]
    AIFLeverageArticle242 = SubElement(AIFLeverageInfo, 'AIFLeverageArticle24-2')

    AllCounterpartyCollateralRehypothecationFlag_value = 'false'
    AllCounterpartyCollateralRehypothecationFlag = SubElement(AIFLeverageArticle242, 'AllCounterpartyCollateralRehypothecationFlag')
    AllCounterpartyCollateralRehypothecationFlag.text = AllCounterpartyCollateralRehypothecationFlag_value
    table_leverage.append(['281', 'Rehypothecation flag', AllCounterpartyCollateralRehypothecationFlag_value])

    FinancialInstrumentBorrowing = SubElement(AIFLeverageArticle242, 'FinancialInstrumentBorrowing')

    ExchangedTradedDerivativesExposureValue_value = str(int(df_aggr.loc[(df_aggr['prod_type'] == 'Future') &
                                                                        (df_aggr['side'] == 'S'), 'notional_usd'].sum()))

    OTCDerivativesAmount_value = str(int(df_aggr.loc[(df_aggr['prod_type'] == 'Cash') &
                                                     (df_aggr['side'] == 'S') &
                                                     (~df_aggr['country'].isin(security_country_list)), 'notional_usd'].sum()))

    ShortPositionBorrowedSecuritiesValue_value = str(int(df_aggr.loc[(df_aggr['prod_type'] == 'Cash') &
                                                                     (df_aggr['side'] == 'S') &
                                                                     (df_aggr['country'].isin(security_country_list)), 'notional_usd'].sum()))

    ExchangedTradedDerivativesExposureValue = SubElement(FinancialInstrumentBorrowing, 'ExchangedTradedDerivativesExposureValue')
    ExchangedTradedDerivativesExposureValue.text = ExchangedTradedDerivativesExposureValue_value
    table_leverage.append(['287', 'Exchange traded derivatives exposure amount', ExchangedTradedDerivativesExposureValue_value])

    OTCDerivativesAmount = SubElement(FinancialInstrumentBorrowing, 'OTCDerivativesAmount')
    OTCDerivativesAmount.text = OTCDerivativesAmount_value
    table_leverage.append(
        ['288', 'OTC derivatives exposure amount', OTCDerivativesAmount_value])

    ShortPositionBorrowedSecuritiesValue = SubElement(AIFLeverageArticle242, 'ShortPositionBorrowedSecuritiesValue')
    ShortPositionBorrowedSecuritiesValue.text = ShortPositionBorrowedSecuritiesValue_value
    table_leverage.append(
        ['289', 'Short Position Borrowed Securities Value', ShortPositionBorrowedSecuritiesValue_value])

    if NAV_USD == 0:
        GrossMethodRate_value = str(1)
    else:
        GrossMethodRate_value = str(round(AUM_USD / NAV_USD, 2))
    LeverageAIF = SubElement(AIFLeverageArticle242, 'LeverageAIF')
    GrossMethodRate = SubElement(LeverageAIF, 'GrossMethodRate')
    GrossMethodRate.text = GrossMethodRate_value
    table_leverage.append(
        ['294', 'Leverage under gross method', GrossMethodRate_value])

    CommitmentMethodRate_value = GrossMethodRate_value  # Owen confirm that is fine to use the same method
    CommitmentMethodRate = SubElement(LeverageAIF, 'CommitmentMethodRate')
    CommitmentMethodRate.text = CommitmentMethodRate_value
    table_leverage.append(
        ['295', 'Leverage under commitment method', CommitmentMethodRate_value])

    html += list_to_html_table(table_leverage, 'Leverage (N271-295)')

    html += f'<H1><u>24.4 for {my_fund}</u><H2>'
    table_borrowing = [['Ranking', 'Borrowing Flag', 'Source Name', 'Source LEI', 'Leverage Amount']]

    AIFLeverageArticle244 = SubElement(AIFLeverageInfo, 'AIFLeverageArticle24-4')

    my_sql = f"""SELECT round(sum(abs(mkt_value_usd)*qty_gs/quantity),0) as GS,round(sum(abs(mkt_value_usd)*qty_ms/quantity),0) as MS,
    round(sum(abs(mkt_value_usd)*qty_ubs/quantity),0) as UBS FROM position T1 
                 WHERE T1.entry_date='{end_date}' and parent_fund_id in {fund_id_list} and quantity<0;"""
    df_cpty = pd.read_sql(my_sql, con=engine)

    LeverageAmount_GS = df_cpty['GS'].sum()
    LeverageAmount_MS = df_cpty['MS'].sum()
    LeverageAmount_UBS = df_cpty['UBS'].sum()

    for index, pb in enumerate(pbs):

        if pb[0] == 'GS':
            LeverageAmount = LeverageAmount_GS
        elif pb[0] == 'MS':
            LeverageAmount = LeverageAmount_MS
        elif pb[0] == 'UBS':
            LeverageAmount = LeverageAmount_UBS

        BorrowingSource = SubElement(AIFLeverageArticle244, 'BorrowingSource')
        Ranking_value = str(index + 1)
        Ranking = SubElement(BorrowingSource, 'Ranking')
        Ranking.text = Ranking_value

        BorrowingSourceFlag_value = 'true'
        BorrowingSourceFlag = SubElement(BorrowingSource, 'BorrowingSourceFlag')
        BorrowingSourceFlag.text = BorrowingSourceFlag_value

        SourceIdentification = SubElement(BorrowingSource, 'SourceIdentification')
        EntityName_value = pb[1]
        EntityName = SubElement(SourceIdentification, 'EntityName')
        EntityName.text = EntityName_value

        EntityIdentificationLEI = SubElement(SourceIdentification, 'EntityIdentificationLEI')
        EntityIdentificationLEI_value = pb[2]
        EntityIdentificationLEI.text = EntityIdentificationLEI_value

        LeverageAmount_value = str(int(LeverageAmount))
        LeverageAmount = SubElement(BorrowingSource, 'LeverageAmount')
        LeverageAmount.text = LeverageAmount_value

        table_borrowing.append([Ranking_value, BorrowingSourceFlag_value, EntityName_value,
                                EntityIdentificationLEI_value, LeverageAmount_value])

    # add missing rank
    rows_num = len(pbs)
    if rows_num < 5:
        for i in range(rows_num + 1, 6):
            BorrowingSource = SubElement(AIFLeverageArticle244, 'BorrowingSource')
            Ranking_value = str(i)
            Ranking = SubElement(BorrowingSource, 'Ranking')
            Ranking.text = Ranking_value

            BorrowingSourceFlag_value = 'false'
            BorrowingSourceFlag = SubElement(BorrowingSource, 'BorrowingSourceFlag')
            BorrowingSourceFlag.text = BorrowingSourceFlag_value

            table_borrowing.append([Ranking_value, BorrowingSourceFlag_value, '', '', ''])

    html += list_to_html_table(table_borrowing, 'Borrowing (N296-301)')

    output = prettify(root)
    print(output)
    xml_filename = f"AIF_{my_fund}.xml"
    # with open(xml_filename, "w") as f:
    #    f.write(output)

    tree._setroot(root)
    tree.write(xml_filename, encoding="UTF-8", xml_declaration=True)

    simple_email(f"AIF Report {my_fund} {quarter} {year}", '', 'olivier@ananda-am.com', html, xml_filename)
