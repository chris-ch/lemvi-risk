import csv
from collections import defaultdict
import pandas


def parse_csv_margin_file(file_path):
    with open(file_path, 'r') as file_data:
        result = parse_csv_margin_data(file_data)

    return result


def parse_csv_margin_data(file_data):
    ib_raw_data = defaultdict(list)
    ib_data = defaultdict(list)
    starting_field = None
    for line in file_data:
        fields = line.split(',')
        if fields[0] != starting_field:
            starting_field = fields[0]

        ib_raw_data[starting_field].append(','.join(fields[2:]))

    for category in ib_raw_data:
        lines = ib_raw_data[category]
        ib_data[category] = pandas.DataFrame(list(csv.DictReader(lines)))

    return ib_data


def get_margin_data(ib_margin_data):
    as_of_date = ib_margin_data['Account']['AsOfDateTime'].iloc[0]
    base_currency = ib_margin_data['Account']['BaseCurrency'].iloc[0]
    margin_summary = ib_margin_data['MarginSummary'].set_index('Parameter')['Total']
    net_liquidation_value = round(float((margin_summary['NetLiquidationValue'])))
    cash_value = round(float(margin_summary['CashValue']))
    initial_margin_requirement = round(float(margin_summary['InitialMarginRequirement']))
    maintenance_margin_requirement = round(float(margin_summary['MaintenanceMarginRequirement']))
    margin_data = {
        'net_liquidation_value': net_liquidation_value,
        'cash_value': cash_value,
        'initial_margin_requirement': initial_margin_requirement,
        'maintenance_margin_requirement': maintenance_margin_requirement,
        'as_of_date': as_of_date,
        'base_currency': base_currency
    }
    return margin_data

