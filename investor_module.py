import pandas as pd
from models import engine, session, CurrencyHistory, InvestorCapital, NavAccountStatement, FundFee
from datetime import date, timedelta
from utils import previous_quarter

def get_main_beneficial_owners():

    my_date = date.today()
    _, _, end_date = previous_quarter(my_date)
    report_date = session.query(InvestorCapital.entry_date).filter(InvestorCapital.entry_date<=end_date).\
                                     order_by(InvestorCapital.entry_date.desc()).first()[0]

    fx_rate_db = session.query(CurrencyHistory).filter(CurrencyHistory.entry_date == report_date).all()
    rate_eur = [fxh.rate for fxh in fx_rate_db if fxh.currency.code == 'EUR'][0]
    rate_gbp = [fxh.rate for fxh in fx_rate_db if fxh.currency.code == 'GBP'][0]

    # get end balance
    my_sql = f"""SELECT T3.name as investor,T4.code as cncy,sum(ending_balance*ending_per/100) as balance
FROM investor_alloc T1 JOIN investor_capital T2 on T1.investor_capital_id=T2.id JOIN investor T3 on T1.investor_id=T3.id
JOIN Currency T4 on T2.cncy_id=T4.id WHERE (ending_balance!=0 or additions!=redemptions) and entry_date='{report_date}'
GROUP by T3.name,T4.code order by T3.name"""

    df_balance = pd.read_sql(my_sql, con=engine)
    investor_list = df_balance['investor'].unique()
    df = pd.DataFrame(index=investor_list)

    df_balance['rate'] = df_balance['cncy'].apply(lambda x: rate_eur if x == 'EUR' else rate_gbp if x == 'GBP' else 1)
    df_balance['balance USD'] = df_balance['balance'] / df_balance['rate']

    # get sum of all investors
    total_sum = df_balance['balance USD'].sum()
    # remove the investor 'Ananda Asset Management Ltd' from the dataframe
    df_balance = df_balance[df_balance['investor'] != 'Ananda Asset Management Ltd']

    # group by investor
    df_balance = df_balance.groupby(['investor']).agg({'balance USD': 'sum'})
    # sort by balance desc
    df_balance = df_balance.sort_values(by='balance USD', ascending=False)
    # get sum of top 5 investors
    top5_sum = df_balance['balance USD'].head(5).sum()
    # get rate of top 5 investors
    top5_rate = top5_sum / total_sum
    top5_rate_formatted = round(top5_rate*100, 2)
    return top5_rate_formatted


def month_end_dates(start_date, end_date):
    current_date = start_date.replace(day=1)
    month_ends = []
    while current_date <= end_date:
        next_month = (current_date + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        if month_end <= end_date:
            month_ends.append(month_end)
        current_date = next_month
    return month_ends


def get_return_alto():
    my_date = date.today()
    # my_date = date(2022, 4, 1)
    quarter, start_date, end_date = previous_quarter(my_date)
    month_ends = month_end_dates(start_date, end_date)

    # find class F fees
    fund_fee = session.query(FundFee).filter(FundFee.entry_date <= end_date).\
        filter(FundFee.fee_type == 'Management').filter(FundFee.class_type == 'F').\
        order_by(FundFee.entry_date.desc()).first()
    fee_rate = fund_fee.value
    fee_rate_month = round(fee_rate / 12, 2)

    # find the class F USD month end report for each date
    GrossInvestmentReturnsRate_alto = []
    NetInvestmentReturnsRate_alto = []
    NAVChangeRate_alto = []
    for my_date in month_ends:
        nav_report = session.query(NavAccountStatement).filter(NavAccountStatement.entry_date <= my_date).\
            filter(NavAccountStatement.status == 'MonthEnd').filter(NavAccountStatement.data_name == 'RETURN USD CLASS F').\
            order_by(NavAccountStatement.entry_date.desc()).filter(NavAccountStatement.active == 1).first()
        net_monthly_return = nav_report.data_mtd
        gross_monthly_return = round(net_monthly_return + fee_rate_month, 2)
        GrossInvestmentReturnsRate_alto.append(gross_monthly_return)
        NetInvestmentReturnsRate_alto.append(net_monthly_return)
        NAVChangeRate_alto.append(net_monthly_return)

    return GrossInvestmentReturnsRate_alto, NetInvestmentReturnsRate_alto, NAVChangeRate_alto


def get_subscription_redemption_alto():
    my_date = date.today()
    # my_date = date(2022, 4, 1)
    quarter, start_date, end_date = previous_quarter(my_date)
    month_ends = month_end_dates(start_date, end_date)

    Subscription_alto, Redemption_alto = [], []
    for my_date in month_ends:
        investor_capital = session.query(InvestorCapital).filter(InvestorCapital.entry_date <= my_date).\
            order_by(InvestorCapital.entry_date.desc()).first()
        report_date = investor_capital.entry_date
        my_sql = f"""SELECT T3.name as investor,T3.id as investor_id,T4.code as cncy,sum(additions*additions_per/100) as additions,
        sum(redemptions*redemptions_per/100) as redemptions,min(entry_date) as min_date,max(entry_date) as max_date
        FROM investor_alloc T1 JOIN investor_capital T2 on T1.investor_capital_id=T2.id JOIN investor T3 on T1.investor_id=T3.id
        JOIN Currency T4 on T2.cncy_id=T4.id WHERE (ending_balance!=0 or additions!=redemptions) AND entry_date='{report_date}'
        GROUP by T3.name,T4.code order by T3.name"""
        df_add_red = pd.read_sql(my_sql, con=engine)

        fx_rate_db = session.query(CurrencyHistory).filter(CurrencyHistory.entry_date == report_date).all()
        rate_eur = [fxh.rate for fxh in fx_rate_db if fxh.currency.code == 'EUR'][0]
        rate_gbp = [fxh.rate for fxh in fx_rate_db if fxh.currency.code == 'GBP'][0]

        df_add_red['rate'] = df_add_red['cncy'].apply(lambda x: rate_eur if x == 'EUR' else rate_gbp if x == 'GBP' else 1)
        df_add_red['additions USD'] = df_add_red['additions'] / df_add_red['rate']
        df_add_red['redemptions USD'] = df_add_red['redemptions'] / df_add_red['rate']
        additions_sum = df_add_red['additions USD'].sum()
        Subscription_alto.append(additions_sum)
        redemptions_sum = df_add_red['redemptions USD'].sum()
        Redemption_alto.append(redemptions_sum)
    return Subscription_alto, Redemption_alto


MainBeneficialOwnersRate_alto = get_main_beneficial_owners()
GrossInvestmentReturnsRate_alto, NetInvestmentReturnsRate_alto, NAVChangeRate_alto = get_return_alto()
Subscription_alto, Redemption_alto = get_subscription_redemption_alto()

if __name__ == '__main__':
    print(MainBeneficialOwnersRate_alto)
    GrossInvestmentReturnsRate_alto, NetInvestmentReturnsRate_alto, NAVChangeRate_alto = get_return_alto()
