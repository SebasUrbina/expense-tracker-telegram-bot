from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY = 'credentials.json'

# Configuración del logger al inicio del archivo
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GoogleSheets:
    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=SCOPES)

    service = build('sheets', 'v4', credentials=creds)

    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.sheet = self.service.spreadsheets()

    def append_expenses(self, values: list[list[str]]):
        result = (
            self.sheet
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range='Records!A1',
                valueInputOption='USER_ENTERED',
                body={'values': values})
            .execute()
        )

        logger.info(f"Datos insertados correctamente.\n{(result.get('updates').get('updatedCells'))}")

        return result.get('updates').get('updatedRange')

    def delete_expense(self, range: str):
        result = (
            self.sheet
            .values()
            .clear(
                spreadsheetId=self.spreadsheet_id,
                range=range
            )
            .execute()
        )
        logger.info(f"Datos eliminados correctamente. Rango: {result.get("clearedRange")}")
