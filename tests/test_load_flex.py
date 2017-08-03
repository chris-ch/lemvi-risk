import unittest
import os
import logging

from datetime import date

from decimal import Decimal

from ibrokersflex import parse_flex_accounts, parse_flex_positions, parse_flex_flows


class LoadFlexResultsTestCase(unittest.TestCase):
    def setUp(self):
        self.tree = None
        example_file_path = os.path.abspath(os.sep.join(['tests-data', 'example-result.xml']))
        logging.info('loading example result file: {}'.format(example_file_path))
        with open(example_file_path, 'r') as result_content:
            lines = result_content.readlines()
            content = ''.join(lines)
            self.content = content

    def test_load_accounts(self):
        accounts = parse_flex_accounts(self.content)
        self.assertEqual(accounts['U1812119']['nav_change'], -67697)
        self.assertEqual(accounts['U1812946']['account_alias'], 'Vol 946')
        self.assertEqual(accounts['U1812119']['cash'], 1350944)
        self.assertEqual(accounts['U1812946']['cash'], 1511983)
        total_cash = 0.
        total_nav = 0.
        for account_code in accounts:
            total_cash += accounts[account_code]['cash']
            total_nav += accounts[account_code]['nav_end']

        self.assertAlmostEqual(total_cash, 7805555, places=0)
        self.assertAlmostEqual(total_nav, 11699176, places=0)

    def test_load_flows(self):
        flows_none = parse_flex_flows(self.content, indicator='Translations', currency='USD')
        self.assertIsNone(flows_none)
        flows = parse_flex_flows(self.content, indicator='Translations', currency='EUR')
        self.assertFalse(date(2017, 8, 2) in flows.index)
        self.assertTrue(date(2017, 8, 1) in flows.index)
        result = flows.loc[date(2017, 8, 1)]
        expected = {
            'U1760542': Decimal('1007.508474'),
            'U1812038': Decimal('3971.417343'),
            'U1812091': Decimal('-1851.280363'),
            'U1812119': Decimal('2112.43022'),
            'U1812946': Decimal('1661.541465'),
            'U1812955': Decimal('45.861602'),
            'U1932389': Decimal('54.865626'),
            'U1935148': Decimal('-255.148445'),
            'U2036485': Decimal('1469.745805'),
            'U2075304': Decimal('186.957103'),
            'U2106037': Decimal('278.897959'),
            'U2157441': Decimal('473.0886'),
        }
        self.assertDictEqual(result.to_dict(), expected)

    def test_load_positions(self):
        positions = parse_flex_positions(self.content)
        self.assertEqual(positions['U1760542']['132757576']['description'], 'EUR 18SEP17')
        self.assertEqual(positions['U1812038']['215313814']['description'], 'BAX 17DEC18')
        self.assertEqual(positions['U1812038']['119750055']['currency'], 'USD')
        self.assertEqual(positions['U1812038']['259910541']['assetCategory'], 'FUT')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    unittest.main()
