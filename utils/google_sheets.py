import os
import base64
import json
from typing import List, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _build_credentials():
    """Crea credenciales desde variable de entorno base64."""
    credentials_base64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
    
    if not credentials_base64:
        raise ValueError("GOOGLE_CREDENTIALS_BASE64 no está definido")
    
    try:
        # Decodificar el base64
        credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
        credentials_info = json.loads(credentials_json)
        
        return service_account.Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
    except Exception as e:
        raise ValueError(f"Error decodificando credenciales: {e}")

def _get_sheets_service():
    """Obtiene el servicio de Google Sheets."""
    credentials = _build_credentials()
    return build("sheets", "v4", credentials=credentials).spreadsheets()

def append_row(spreadsheet_id: str, sheet_name: str, row_values: List[Optional[str]]):
    """
    Inserta una fila al final de la hoja especificada.
    """
    if not spreadsheet_id or not sheet_name:
        raise ValueError("spreadsheet_id y sheet_name son requeridos")

    sheets = _get_sheets_service()
    
    range_name = f"{sheet_name}!A:AS"
    values = [row_values]

    request = sheets.values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": values},
    )
    return request.execute()