from bs4 import BeautifulSoup
import requests

_PRODUCTS_URL = 'https://pennies.interactivebrokers.com/cstools/contract_info/v3.9/index.php'
_URL_TEMPLATE = _PRODUCTS_URL + '?action=Conid%20Info&wlId=IB&conid={}&lang=en'


def load_search_page(con_id):
    target_url = _URL_TEMPLATE.format(con_id)
    session = requests.Session()
    response = session.get(target_url)
    return response.content


def search_product(page_content):
    page = BeautifulSoup(page_content, 'html.parser')
    keepers = ('Futures Features', 'Contract Identifiers', 'Contract Information', 'Underlying Information', 'Margin Requirements')
    product_data = dict()
    for table in page.find_all('table', {'class': 'resultsTbl'}):
        label_row = table.find_next('tr')
        if label_row:
            label_tag = label_row.find('th')
            if label_tag and label_tag.text in keepers:
                fields = list()
                for row in table.find_all('tr'):
                    for field in row.find_all('td'):
                        fields.append(field.text)

                names = fields[0:][::2]
                values = fields[1:][::2]
                product_data[label_tag.text] = dict(zip(names, values))

    return product_data