from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging
from typing import List
from utils.utils import setup_logger

# Constantes en mayúsculas al inicio del módulo
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = "credentials.json"
SHEET_RANGE = "Records!A1"
VALUE_INPUT_OPTION = "USER_ENTERED"

# Configuración del logger usando un formato más descriptivo
logger = setup_logger(__name__)


class GoogleSheets:
    """
    Clase para manejar operaciones con Google Sheets API.

    Attributes:
        spreadsheet_id (str): ID del documento de Google Sheets
        sheet: Objeto de la API de Google Sheets
    """

    def __init__(self, spreadsheet_id: str) -> None:
        """
        Inicializa una nueva instancia de GoogleSheets.

        Args:
            spreadsheet_id (str): ID del documento de Google Sheets
        """
        self.spreadsheet_id = spreadsheet_id
        self._initialize_service()

    def _initialize_service(self) -> None:
        """Inicializa el servicio de Google Sheets."""
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)
        self.sheet = service.spreadsheets()

    def append_expenses(self, values: List[List[str]]) -> str:
        """
        Añade gastos al documento de Google Sheets.

        Args:
            values (List[List[str]]): Lista de filas para añadir

        Returns:
            str: Rango actualizado

        Raises:
            Exception: Si hay un error al insertar los datos
        """
        try:
            result = (
                self.sheet.values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=SHEET_RANGE,
                    insertDataOption="INSERT_ROWS",
                    valueInputOption=VALUE_INPUT_OPTION,
                    body={"values": values},
                )
                .execute()
            )

            updated_cells = result.get("updates", {}).get("updatedCells", 0)
            logger.info(
                f"Datos insertados correctamente. Celdas actualizadas: {updated_cells}"
            )

            return result.get("updates", {}).get("updatedRange", "")

        except Exception as e:
            logger.error(f"Error al insertar datos: {str(e)}")
            raise

    def delete_expense(self, range_: str) -> None:
        """
        Elimina gastos del rango especificado.

        Args:
            range_ (str): Rango de celdas a eliminar

        Raises:
            Exception: Si hay un error al eliminar los datos
        """
        try:
            result = (
                self.sheet.values()
                .clear(spreadsheetId=self.spreadsheet_id, range=range_)
                .execute()
            )

            cleared_range = result.get("clearedRange", "")
            logger.info(f"Datos eliminados correctamente. Rango: {cleared_range}")

        except Exception as e:
            logger.error(f"Error al eliminar datos: {str(e)}")
            raise
