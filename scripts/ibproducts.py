import logging
import argparse

from pprint import pprint

from searchproduct import search_product, load_search_page


def main(args):
    con_id = '247950613'
    page_content = load_search_page(con_id)
    pprint(search_product(page_content))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler = logging.FileHandler('ibproducts.log', mode='w')
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    logging.info('starting script')
    parser = argparse.ArgumentParser(description='Looking up product information on IBrokers website',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)


    args = parser.parse_args()
    main(args)
