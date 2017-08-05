import logging
import httplib2
import pygsheets
from apiclient import discovery
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


def create_service_sheets(credentials):
    sheets_client = pygsheets.Client(oauth=credentials)
    return sheets_client