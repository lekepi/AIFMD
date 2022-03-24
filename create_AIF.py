from datetime import date, datetime
from models import engine
from utils import previous_quarter
from xml.etree.ElementTree import Element, SubElement, Comment
import pandas as pd
from utils import prettify

from manual_data import EURUSD_RATE, AUM_ALTO_USD, AUM_NEUTRAL_USD


def create_aif(my_fund):
    today = date.today()
    quarter, start_date, end_date = previous_quarter(today)
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    root = Element('AIFMReportingInfo', {'CreationDateAndTime': f'{now_str}',
                                         'Version': '1.2',
                                         'ReportingMemberState': 'GB',
                                         'xsi:noNamespaceSchemaLocation': 'AIFMD_DATMAN_V1.2.xsd',
                                         'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'})

    output = prettify(root)

    with open(f"AIF_{my_fund}.xml", "w") as f:
        f.write(output)
