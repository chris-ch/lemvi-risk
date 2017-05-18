import unittest
import os
import logging

from ibrokersflex import parse_flex_result


class LoadResultsTestCase(unittest.TestCase):

    def setUp(self):
        self.tree = None
        example_file_path = os.path.abspath(os.sep.join(['tests-data', 'example-result.xml']))
        logging.info('loading example result file: {}'.format(example_file_path))
        with open(example_file_path, 'r') as result_content:
            lines = result_content.readlines()
            content = ''.join(lines)
            self.content = content

    def test_load_example(self):
        accounts = parse_flex_result(self.content)
        self.assertEquals(accounts['U1812119']['nav_change'], -39536)
        self.assertEquals(accounts['U1812946']['account_alias'], 'Vol 946')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
