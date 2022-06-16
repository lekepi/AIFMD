from datetime import date
from utils import prettify, list_to_html_table, find_active_contract
from models import session, Product


EXPI_MONTH = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']


if __name__ == '__main__':
    my_date = date(2021, 12, 31)
    # product = find_active_contract('SXO1 CME', my_date)
    product = find_active_contract('ES1 CME', my_date)

    print(product.name)
