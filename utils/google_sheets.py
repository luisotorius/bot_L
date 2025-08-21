import os
from typing import List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _build_credentials() -> service_account.Credentials:
    """Crea credenciales desde un archivo de cuenta de servicio.

    Prioriza la variable de entorno GOOGLE_SERVICE_ACCOUNT_FILE; como fallback
    usa GOOGLE_APPLICATION_CREDENTIALS.
    """
    credentials_file = (
        os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )
    if not credentials_file or not os.path.exists(credentials_file):
        raise FileNotFoundError(
            "No se encontró el archivo de credenciales de Google. "
            "Defina GOOGLE_SERVICE_ACCOUNT_FILE o GOOGLE_APPLICATION_CREDENTIALS con la ruta del JSON."
        )

    return service_account.Credentials.from_service_account_file(
        credentials_file, scopes=SCOPES
    )


def _get_sheets_service():
    credentials = _build_credentials()
    service = build("sheets", "v4", credentials=credentials)
    return service.spreadsheets()


def append_row(spreadsheet_id: str, sheet_name: str, row_values: List[Optional[str]]):
    """Inserta una fila al final de la hoja especificada de manera segura para múltiples usuarios."""
    if not spreadsheet_id:
        raise ValueError("spreadsheet_id es requerido")
    if not sheet_name:
        raise ValueError("sheet_name es requerido")

    sheets = _get_sheets_service()
    
    # Estrategia: usar append con inserción de fila
    # INSERT_ROWS asegura que Google Sheets maneje la concurrencia internamente
    range_name = f"{sheet_name}!B:AT"
    values = [row_values]

    request = sheets.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    )
    return request.execute()
