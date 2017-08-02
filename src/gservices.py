import logging
import httplib2
from apiclient import discovery
from gspread.utils import rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials

_GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'
_GOOGLE_DRIVE_FILE_SCOPE = 'https://www.googleapis.com/auth/drive.file'


def file_by_id(svc_drive, file_id):
    response = svc_drive.files().get(fileId=file_id)
    return response.execute()


def authorize_services(credentials_json):
    """

    :param credentials_json:
    :return:
    """
    scopes = [_GOOGLE_DRIVE_SCOPE]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_json, scopes)
    if not credentials or credentials.invalid:
        raise Exception('Invalid credentials')

    logging.info('using Google service account {} (project {})'.format(credentials_json['client_email'], credentials_json['project_id']))
    authorized_http = credentials.authorize(httplib2.Http())
    return authorized_http, credentials


def setup_services(credentials_json):
    """
    :param credentials_json: Google JSON Service Account credentials
    :return: tuple (Drive service, Sheets service)
    """
    authorized_http, credentials = authorize_services(credentials_json)
    svc_drive = discovery.build('drive', 'v3', http=authorized_http, cache_discovery=False)
    svc_sheets = discovery.build('sheets', 'v4', http=authorized_http, cache_discovery=False)
    return svc_drive, svc_sheets


def save_sheet(svc_sheet, spreadsheet_id, tab_name, header, records):
    """
    Saves indicated records to sheet.

    :param svc_sheet:
    :param spreadsheet_id:
    :param tab_name:
    :param header:
    :param records: list of dict to be saved (records-like format)
    :return:
    """
    if len(records) == 0:
        return

    count_columns = len(header)
    count_rows = len(records) + 1
    workbook = svc_sheet.open_by_key(spreadsheet_id)
    sheets = dict()
    for sheet in workbook.worksheets():
        sheets[sheet.title] = sheet

    if tab_name not in sheets:
        worksheet = workbook.add_worksheet(tab_name, count_rows, count_columns)

    else:
        worksheet = sheets[tab_name]

    worksheet.resize(rows=count_rows, cols=count_columns)
    range_text = 'A1:{}'.format(rowcol_to_a1(count_rows, count_columns))
    logging.info('accessing range {}'.format(range_text))
    cells = worksheet.range(range_text)
    for cell in cells:
        count_row = cell.row - 1
        count_col = cell.col - 1
        field = header[count_col]
        if count_row == 0:
            cell.value = field

        else:
            row_data = records[count_row - 1]
            cell.value = row_data[field]

    worksheet.update_cells(cells)
