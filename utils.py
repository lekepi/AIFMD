from datetime import date
from xml.etree import ElementTree
from xml.dom import minidom
from models import config_class, session, Product
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import pandas as pd
from models import engine, PositionNav

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