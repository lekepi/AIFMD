from datetime import date
from xml.etree import ElementTree
from xml.dom import minidom
from models import config_class, session, Product
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders
import smtplib

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
    rough_string = ElementTree.tostring(elem, 'utf-8')
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
    month = int(my_date.strftime("%m"))
    month_letter = EXPI_MONTH[month - 1]
    year = my_date.year % 10

    active_ticker = ticker.replace("1", f'{month_letter}{year}')
    products = [prod for prod in product_db if prod.ticker == active_ticker]
    if products:
        return products[0]
    else:
        return None