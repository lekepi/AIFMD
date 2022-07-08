from datetime import date
from xml.etree import ElementTree
from xml.dom import minidom
from models import config_class, session, Product, engine, PositionNav, InvestorActivity
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import pandas as pd

EXPI_MONTH = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']


def previous_quarter(ref):
    if ref.month < 4:
        return 'Q4', date(ref.year - 1, 10, 1), date(ref.year - 1, 12, 31)
    elif ref.month < 7:
        return 'Q1', date(ref.year, 1, 1), date(ref.year, 3, 31)
    elif ref.month < 10:
        return 'Q2', date(ref.year, 4, 1), date(ref.year, 6, 30)
    return 'Q3', date(ref.year, 7, 1), date(ref.year, 9, 30)


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ElementTree.tostring(elem, encoding='utf8', method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def simple_email(subject, body, ml, html=None, filename=''):

    mail = config_class.MAIL_USERNAME
    password = config_class.MAIL_PASSWORD

    msg = EmailMessage()
    msg['subject'] = subject
    msg['From'] = 'ananda.am.system@gmail.com'
    msg['To'] = ml  # multiple email: 'olivier@ananda-am.com, lekepi@gmail.com'
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype='html')

    if filename != '':
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(filename, "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(mail, password)
        smtp.send_message(msg)


def list_to_html_table(my_lists, title=''):

    html = f'<h2>{title}</h2>'
    html += '''<table border="1" class="dataframe">
                  <thead>
                    <tr style="text-align:right;background-color:#D3D3D3;">'''
    for element in my_lists[0]:
        html += f"<th> {element}</th>"
    html += '''</tr>
                  </thead>
                  <tbody>'''

    for index, my_list in enumerate(my_lists):
        if index > 0:
            html += "<tr>"
            for element in my_list:
                html += f"<td>{element}</td>"
            html += "</tr>"

    html += "</tbody></table><br/>"
    return html


def find_active_contract(ticker, my_date):

    product_db = session.query(Product).all()
    prod_gen = [prod for prod in product_db if prod.ticker == ticker]
    if prod_gen:
        sec_expi_months = prod_gen[0].security.expi_months
    else:
        sec_expi_months = "HMUZ"

    month = int(my_date.strftime("%m")) % 12 + 1

    while EXPI_MONTH[month-1] not in sec_expi_months:
        month += 1

    month_letter = EXPI_MONTH[month-1]
    year = my_date.year % 10

    active_ticker = ticker.replace("1", f'{month_letter}{year}')
    products = [prod for prod in product_db if prod.ticker == active_ticker]
    if products:
        return products[0]
    else:
        return None

def find_active_contract_old(ticker, my_date):

    product_db = session.query(Product).all()
    month = int(my_date.strftime("%m"))
    month_letter = EXPI_MONTH[month - 1]
    year = my_date.year % 10

    active_ticker = ticker.replace("1", f'{month_letter}{year}')
    products = [prod for prod in product_db if prod.ticker == active_ticker]
    if products:
        return products[0]
    else:
        return None

def get_asset_list(my_date):
    my_sql = f"""SELECT T1.entry_date,T5.parent as fund,T3.name as pb,T2.prod_type,is_cfd,round(sum(notional_usd),2) as Notional_usd FROM position_pb T1 
    JOIN product T2 on T1.product_id=T2.id JOIN parent_broker T3 on T1.parent_broker_id=T3.id
    JOIN account T4 on T1.account_id=T4.id JOIN fund T5 on T4.fund_id=T5.id
    WHERE T1.entry_date='{my_date}' GROUP BY T1.entry_date,T5.parent,T3.name,T2.prod_type,is_cfd
    ORDER BY T1.entry_date,T5.parent,T3.name,T2.prod_type,is_cfd;"""
    df = pd.read_sql(my_sql, con=engine)
    if df.empty:
        return ['GS', 0, 0, 0, 0], ['MS', 0, 0, 0, 0], ['UBS', 0, 0, 0, 0]

    gs_cash = 0
    gs_stock = 0
    gs_cfd = 0
    if not df[(df['pb'] == 'GS')].empty:
        gs_cash_list = df[(df['pb'] == 'GS') & (df['fund'] == 'Alto') &
                          (df['prod_type'] == 'FX Cash')]['Notional_usd'].values
        if gs_cash_list: gs_cash = gs_cash_list[0]
        gs_stock_list = df[(df['pb'] == 'GS') & (df['fund'] == 'Alto') &
                           (df['prod_type'] == 'Cash') & (df['is_cfd'] == 0)]['Notional_usd'].values
        if gs_stock_list: gs_stock = gs_stock_list[0]
        gs_cfd_list = df[(df['pb'] == 'GS') & (df['fund'] == 'Alto') &
                         (df['prod_type'] == 'Cash') & (df['is_cfd'] == 1)]['Notional_usd'].values
        if gs_cfd_list: gs_cfd = gs_cfd_list[0]

    ms_cash = 0
    ms_stock = 0
    ms_cfd = 0
    if not df[(df['pb'] == 'MS')].empty:
        ms_cash_list = df[(df['pb'] == 'MS') & (df['fund'] == 'Alto') &
                          (df['prod_type'] == 'FX Cash')]['Notional_usd'].values
        if ms_cash_list: ms_cash = ms_cash_list[0]
        ms_stock_list = df[(df['pb'] == 'MS') & (df['fund'] == 'Alto') &
                           (df['prod_type'] == 'Cash') & (df['is_cfd'] == 0)]['Notional_usd'].values
        if ms_stock_list: ms_stock = ms_stock_list[0]

        ms_cfd_list = df[(df['pb'] == 'MS') & (df['fund'] == 'Alto') &
                         (df['prod_type'] == 'Cash') & (df['is_cfd'] == 1)]['Notional_usd'].values
        if ms_cfd_list: ms_cfd = ms_cfd_list[0]

    ubs_cash = 0
    ubs_stock = 0
    ubs_cfd = 0
    if not df[(df['pb'] == 'UBS')].empty:
        ubs_cash_list = df[(df['pb'] == 'UBS') & (df['fund'] == 'Neutral') &
                           (df['prod_type'] == 'FX Cash')]['Notional_usd'].values
        if ubs_cash_list: ubs_cash = ubs_cash_list[0]
        ubs_stock_list = df[(df['pb'] == 'UBS') & (df['fund'] == 'Neutral') &
                            (df['prod_type'] == 'Cash') & (df['is_cfd'] == 0)]['Notional_usd'].values
        if ubs_stock_list: ubs_stock = ubs_stock_list[0]
        ubs_cfd_list = df[(df['pb'] == 'UBS') & (df['fund'] == 'Neutral') &
                          (df['prod_type'] == 'Cash') & (df['is_cfd'] == 1)]['Notional_usd'].values
        if ubs_cfd_list: ubs_cfd = ubs_cfd_list[0]

    money_market = session.query(PositionNav).filter(PositionNav.product_id == 552). \
        order_by(PositionNav.entry_date.desc()).first()
    money_market_amount = money_market.notional_nav_usd

    gs_asset = ['GS', gs_cash, gs_stock, gs_cfd, money_market_amount]
    ms_asset = ['MS', ms_cash, ms_stock, ms_cfd, 0]
    ubs_asset = ['UBS', ubs_cash, ubs_stock, ubs_cfd, 0]

    return gs_asset, ms_asset, ubs_asset


def get_investor_activity(my_fund, start_date, end_date):

    if my_fund == "ALTO":
        long_fund = "Ananda Long Term Opportunities Fund"
    elif my_fund == "NEUTRAL":
        long_fund = "Ananda Market Neutral Fund"

    my_sql = f"""SELECT T1.id,fund_name,activity,effective_date,amount,T2.code as cncy
                 FROM investor_activity T1 LEFT JOIN currency T2 on T1.cncy_id=T2.id
                 WHERE T1.effective_date>='{start_date}' and T1.effective_date<='{end_date}';"""
    df = pd.read_sql(my_sql, con=engine, parse_dates=['effective_date'])
    df = df[df['fund_name'].str.startswith(long_fund)]

    df.loc[df['activity'].str.contains('Addition'), 'activity'] = 'Subscription'
    df.loc[df['activity'].str.contains('Subscription'), 'activity'] = 'Subscription'
    df.loc[df['activity'].str.contains('Redemption'), 'activity'] = 'Redemption'

    df['month'] = pd.DatetimeIndex(df['effective_date']).month

    my_sql = f"""SELECT month(entry_date) as month,T2.code as cncy, rate from currency_history T1 JOIN currency T2 on T1.currency_id=T2.id where entry_date in 
     (SELECT distinct(entry_date) FROM currency_history INNER JOIN (
        SELECT MAX(entry_date) AS maxdate FROM currency_history
        GROUP BY YEAR(entry_date), MONTH(entry_date)
    ) x ON currency_history.entry_date = maxdate WHERE entry_date>='{start_date}' and entry_date<='{end_date}')"""
    df_cncy = pd.read_sql(my_sql, con=engine)

    df = pd.merge(df, df_cncy)
    df['amount_usd'] = df['amount'] / df['rate']

    df_group = df.groupby(['activity', 'month']).agg({'amount_usd': 'sum'}).\
        sort_values(by=['activity', 'month']).reset_index()

    subscription_list = [0, 0, 0]
    redemption_list = [0, 0, 0]

    start_month = start_date.month

    for month in range(start_month, start_month + 3):
        subscription = df_group.loc[(df_group['month'] == month) & (df_group['activity'] == 'Subscription'), 'amount_usd'].values
        if subscription:
            subscription_list[month - start_month] = abs(int(subscription[0]))
        redemption = df_group.loc[(df_group['month'] == month) & (df_group['activity'] == 'Redemption'), 'amount_usd'].values
        if redemption:
            redemption_list[month - start_month] = abs(int(redemption[0]))

    return subscription_list, redemption_list
