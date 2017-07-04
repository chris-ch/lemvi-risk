import time
from functools import lru_cache

from bs4 import BeautifulSoup
import requests
import random
import logging

from webscrapetools import urlcaching

_PRODUCTS_URL = 'https://pennies.interactivebrokers.com/cstools/contract_info/v3.9/index.php'
_URL_TEMPLATE = _PRODUCTS_URL + '?action=Conid%20Info&wlId=IB&conid={}&lang=en'


@lru_cache(maxsize=None)
def load_search_page(con_id):
    waiting_time = random.randrange(10, 20)
    logging.info('waiting {} seconds before requesting data...'.format(waiting_time))
    time.sleep(waiting_time)  # working around IBrokers anti-robots check
    target_url = _URL_TEMPLATE.format(con_id)
    content = urlcaching.open_url(target_url, rejection_marker='please enter the text from the image below')
    #session = requests.Session()
    #response = session.get(target_url)
    #content = response.content

    # TODO: testing if IBrokers returned an anti-robots form
    """
    no result returned: b'</form>\n\n<br>\n<form type="post">\nTo continue please enter the text from the image below\n
    <br>\n<img src="image.php?str=FXatg1">\n
    <!--img src="https://chatsrv1.interactivebrokers.com/cstools/contract_info/v3.8/image.php?str=FXatg1"-->
    <br>\nText: <input type="text" name="filter"><input type=\'hidden\' name=\'action\' value=\'Conid Info\'/>
    <input type=\'hidden\' name=\'conid\' value=\'189284065\'/>\n<input type=\'hidden\' name=\'contract_id\' value=\'\'/>
    <input type=\'hidden\' name=\'noBanner\' value=\'\'/>\n<input type=\'hidden\' name=\'rescnt\' value=\'100\'/>
    ...
    <input type=\'hidden\' name=\'lang\' value=\'en\'/>\n<input type=\'Submit\' value=\'Submit\'/>'
    """
    return content


def search_product(page_content):
    page = BeautifulSoup(page_content, 'html.parser')
    keepers = ('Futures Features', 'Contract Identifiers', 'Contract Information', 'Underlying Information', 'Margin Requirements')
    product_data = dict()
    all_tables = page.find_all('table', {'class': 'resultsTbl'})
    if len(all_tables) == 0:
        message = 'no result returned: {}'.format(page_content)
        logging.warning(message)
        raise Exception(message)

    for table in all_tables:
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