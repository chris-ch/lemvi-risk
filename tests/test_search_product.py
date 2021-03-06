import unittest
import os
import logging

from searchproduct import search_product


class SearchProductTestCase(unittest.TestCase):

    def setUp(self):
        self.tree = None
        example_file_path = os.path.abspath(os.sep.join(['tests-data', 'product_search_result.html']))
        logging.info('loading example result file: {}'.format(example_file_path))
        with open(example_file_path, 'r') as result_content:
            lines = result_content.readlines()
            content = ''.join(lines)
            self.content = content

    def test_extract_example(self):
        result = search_product(self.content)
        self.assertEqual(result['Futures Features']['Last Trading Date'], '15/12/2017')
        self.assertEqual(result['Margin Requirements']['Overnight Initial Margin'], '7,600')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
