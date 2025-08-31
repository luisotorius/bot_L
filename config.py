import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Token del bot (obtenido de @BotFather)
TOKEN = os.getenv('BOT_TOKEN', 'TU_TOKEN_AQUI')

# Proxy opcional para Telegram (http://usuario:pass@host:puerto o socks5://...)
PROXY_URL = os.getenv('PROXY_URL')

# ID de administrador (tu ID de Telegram)
ADMIN_ID = int(os.getenv('ADMIN_ID', '123456789'))

# Configuración de Google Sheets
GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', '')
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Hoja1')

# Credenciales de Google en formato base64 (OBLIGATORIO)
# Esta variable debe contener el contenido del archivo JSON convertido a base64
GOOGLE_CREDENTIALS_BASE64 = os.getenv('GOOGLE_CREDENTIALS_BASE64', '')

# Estados de conversación (para el flujo de recolección de datos)
# Los estados de conversación se gestionan en handlers/commands.py