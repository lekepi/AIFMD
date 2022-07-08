from datetime import date
from utils import prettify, list_to_html_table, find_active_contract, get_investor_activity
from models import session, Product


EXPI_MONTH = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']


if __name__ == '__main__':
    start_date = date(2021, 1, 1)
    end_date = date(2022, 7, 31)
    a, b = get_investor_activity('ALTO', start_date, end_date)
