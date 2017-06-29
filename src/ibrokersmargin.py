import csv
from collections import defaultdict
import pandas


def parse_csv_margin_data(file_path):
    ib_raw_data = defaultdict(list)
    ib_data = defaultdict(list)
    with open(file_path, 'r') as content:
        starting_field = None
        for line in content:
            fields = line.split(',')
            if fields[0] != starting_field:
                starting_field = fields[0]

            ib_raw_data[starting_field].append(','.join(fields[2:]))

        for category in ib_raw_data:
            lines = ib_raw_data[category]
            ib_data[category] = pandas.DataFrame(list(csv.DictReader(lines)))

    return ib_data


def get_margin_data(ib_margin_data):
    margin_summary = ib_margin_data['MarginSummary'].set_index('Parameter')['Total']
    net_liquidation_value = round(float((margin_summary['NetLiquidationValue'])))
    cash_value = round(float(margin_summary['CashValue']))
    initial_margin_requirement = round(float(margin_summary['InitialMarginRequirement']))
    maintenance_margin_requirement = round(float(margin_summary['MaintenanceMarginRequirement']))
    margin_data = {
        'net_liquidation_value': net_liquidation_value,
        'cash_value': cash_value,
        'initial_margin_requirement': initial_margin_requirement,
        'maintenance_margin_requirement': maintenance_margin_requirement
    }
    return margin_data

