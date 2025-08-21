"""
MÓDULO DE COMANDOS PARA BOT DE TELEGRAM
Este módulo maneja la conversación con el usuario para recolectar datos
y enviarlos a Google Sheets. Utiliza el patrón ConversationHandler de python-telegram-bot.
"""

# Importaciones necesarias para el funcionamiento del bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from typing import List

# Importaciones propias de la aplicación
from utils.google_sheets import append_row  # Función para enviar datos a Google Sheets
from config import GOOGLE_SPREADSHEET_ID, GOOGLE_SHEET_NAME  # Configuración de la hoja de cálculo

# DEFINICIÓN DE ESTADOS DE LA CONVERSACIÓN
# Cada estado representa un paso en el flujo de recolección de datos
(
    ENTIDAD,          # Paso 1: Selección de entidad
    FECHA,            # Paso 2: Ingreso de fecha
    SUB_REGION,       # Paso 3: Selección de subregión
    MUNICIPIO,        # Paso 4: Selección de municipio
    PARROQUIA,        # Paso 5: Ingreso de parroquia
    NODO,             # Paso 6: Ingreso de nodo
    CEDULA,           # Paso 7: Ingreso de cédula
    CARGO,            # Paso 8: Selección de cargo
    CORREO,           # Paso 9: Ingreso de correo
    SELECCION_PROYECTOS,  # Paso 10: Selección de proyectos
    RELLENAR_PROYECTO,    # Paso 11: Rellenar datos de cada proyecto
    CONFIRMAR,            # Paso 12: Confirmación y envío
) = range(12)  # Asigna números del 0 al 11 a cada estado

# OPCIONES PREESTABLECIDAS PARA LOS MENÚS DESPLEGABLES
ENTIDADES = ["ZULIA"]  # Lista de entidades disponibles
SUB_REGIONES = ["COL I", "COL II", "CAÑADA PERIJA", "MARA GUAJIRA", "MARACAIBO", "SAN FRANCISCO", "SUR DEL LAGO"]  # Subregiones
MUNICIPIOS = [  # Lista de municipios
  "ALMIRANTE PADILLA",
  "BARALT",
  "CABIMAS",
  "CATATUMBO",
  "COLON",
  "FRANCISCO JAVIER PULGAR",
  "JESUS ENRIQUE LOSSADA",
  "JESUS MARIA SEMPRUN",
  "LA CAÑADA DE URDANETA",
  "LAGUNILLAS",
  "MACHIQUES DE PERIJA",
  "MARA",
  "MARACAIBO",
  "MIRANDA",
  "PAEZ",
  "ROSARIO DE PERIJA",
  "SAN FRANCISCO",
  "SANTA RITA",
  "SIMON BOLIVAR",
  "SUCRE",
  "VALMORES RODRIGUEZ"
]
CARGOS = [  # Lista de cargos disponibles
  "COORDINADOR MUNICIPAL",
  "COORDINADOR NODO",
  "SUPERVISOR DE NODO",
  "VERIFICADOR ENCUESTADOR INTEGRAR"
]

# LISTA DE PROYECTOS DISPONIBLES (definida más adelante en el código)
PROYECTOS = [
    "Proyecto 1", "Proyecto 2", "Proyecto 3",
    "Proyecto 4", "Proyecto 5", "Proyecto 6",
    "Proyecto 7", "Proyecto 8", "Proyecto 9"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Función inicial que comienza la conversación.
    Se ejecuta cuando el usuario envía el comando /start.
    """
    # Limpiar datos de usuario previos para evitar conflictos
    context.user_data.clear()
    
    # Crear teclado con botones para selección de entidad
    keyboard = [[InlineKeyboardButton(ent, callback_data=ent)] for ent in ENTIDADES]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])  # Botón para continuar
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Inicializar dato de entidad y enviar mensaje
    context.user_data["ENTIDAD"] = None
    await update.message.reply_text("👋 Bienvenido.\n\nSeleccione la ENTIDAD:", reply_markup=reply_markup)
    return ENTIDAD  # Pasar al siguiente estado

async def entidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de entidad mediante botones interactivos.
    """
    query = update.callback_query  # Obtener la selección del usuario
    await query.answer()  # Responder a la consulta de callback

    if query.data == "done":
        # Usuario presionó "Done", verificar que haya seleccionado una entidad
        if not context.user_data["ENTIDAD"]:
            await query.edit_message_text("⚠️ Debe seleccionar una ENTIDAD.")
            return ENTIDAD  # Permancer en el mismo estado
        # Continuar al siguiente paso: ingresar fecha
        await query.edit_message_text(f"✅ ENTIDAD seleccionada: {context.user_data['ENTIDAD']}\n\n📅 Ingrese la FECHA (dd/mm/aaaa):")
        return FECHA
    else:
        # Usuario seleccionó una entidad, guardarla y actualizar interfaz
        context.user_data["ENTIDAD"] = query.data
        keyboard = [[InlineKeyboardButton(ent, callback_data=ent)] for ent in ENTIDADES]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 ENTIDAD seleccionada: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ENTIDAD  # Permancer en el mismo estado hasta que presione "Done"

async def fecha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de fecha mediante texto libre.
    """
    context.user_data["FECHA"] = update.message.text  # Guardar fecha ingresada

    # Preparar siguiente paso: selección de subregión con botones
    keyboard = [[InlineKeyboardButton(sr, callback_data=sr)] for sr in SUB_REGIONES]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["SUB_REGION"] = None
    await update.message.reply_text("🌍 Seleccione la SUB REGIÓN OPERATIVA:", reply_markup=reply_markup)
    return SUB_REGION

async def sub_region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de subregión mediante botones interactivos.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["SUB_REGION"]:
            await query.edit_message_text("⚠️ Debe seleccionar una SUB REGIÓN.")
            return SUB_REGION
        
        # Preparar siguiente paso: selección de municipio
        keyboard = [[InlineKeyboardButton(m, callback_data=m)] for m in MUNICIPIOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["MUNICIPIO"] = None
        await query.edit_message_text("🏙 Seleccione el MUNICIPIO:", reply_markup=reply_markup)
        return MUNICIPIO
    else:
        context.user_data["SUB_REGION"] = query.data
        keyboard = [[InlineKeyboardButton(sr, callback_data=sr)] for sr in SUB_REGIONES]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 SUB REGIÓN seleccionada: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SUB_REGION

async def parroquia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de parroquia mediante texto libre.
    """
    context.user_data["PARROQUIA"] = update.message.text
    await update.message.reply_text("🏘 Ingrese el NODO:")
    return NODO

async def municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de municipio mediante botones interactivos.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["MUNICIPIO"]:
            await query.edit_message_text("⚠️ Debe seleccionar un MUNICIPIO.")
            return MUNICIPIO
        await query.edit_message_text(f"✅ MUNICIPIO: {context.user_data['MUNICIPIO']}\n\n🏙 Ingrese la PARROQUIA:")
        return PARROQUIA
    else:
        context.user_data["MUNICIPIO"] = query.data
        keyboard = [[InlineKeyboardButton(m, callback_data=m)] for m in MUNICIPIOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 MUNICIPIO seleccionado: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return MUNICIPIO

async def nodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de nodo mediante texto libre.
    """
    context.user_data["NODO"] = update.message.text
    await update.message.reply_text("🪪 Ingrese la CÉDULA DE IDENTIDAD:")
    return CEDULA

async def cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de cédula mediante texto libre.
    """
    context.user_data["CEDULA"] = update.message.text

    # Preparar siguiente paso: selección de cargo con botones
    keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in CARGOS]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["CARGO"] = None
    await update.message.reply_text("👔 Seleccione el CARGO:", reply_markup=reply_markup)
    return CARGO

async def cargo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de cargo mediante botones interactivos.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["CARGO"]:
            await query.edit_message_text("⚠️ Debe seleccionar un CARGO.")
            return CARGO
        # Ir a solicitar correo electrónico
        await query.edit_message_text("📧 Ingrese su CORREO ELECTRÓNICO:")
        return CORREO
    else:
        context.user_data["CARGO"] = query.data
        keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in CARGOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 CARGO seleccionado: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CARGO

async def correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de correo electrónico mediante texto libre.
    """
    context.user_data["CORREO"] = update.message.text
    
    # Ir a selección de proyectos
    context.user_data["selected_projects"] = []  # Inicializar lista de proyectos seleccionados
    keyboard = []
    for proy in PROYECTOS:
        keyboard.append([InlineKeyboardButton(proy, callback_data=proy)])
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    await update.message.reply_text(
        "✔️ Datos básicos completados.\n\n📌 Seleccione los proyectos en los que participa (puede elegir varios) y luego pulse ✅ Done.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return SELECCION_PROYECTOS

async def seleccionar_proyectos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección múltiple de proyectos mediante botones interactivos.
    """
    query = update.callback_query
    await query.answer()
    seleccion = query.data

    if seleccion == "done":
        proyectos = context.user_data["selected_projects"]
        if not proyectos:
            await query.edit_message_text("⚠️ Debe seleccionar al menos un proyecto.")
            return SELECCION_PROYECTOS

        # Comenzar a recoger datos para el primer proyecto
        context.user_data["current_project_index"] = 0
        await query.edit_message_text(
            f"✍️ Vamos con *{proyectos[0]}*.\n\nIngrese SEGMENTOS TRABAJADOS:",
            parse_mode="Markdown"
        )
        return RELLENAR_PROYECTO

    else:
        # Alternar selección (agregar o quitar)
        if seleccion in context.user_data["selected_projects"]:
            context.user_data["selected_projects"].remove(seleccion)
        else:
            context.user_data["selected_projects"].append(seleccion)

        # Actualizar interfaz con marcas de selección
        keyboard = []
        for proy in PROYECTOS:
            marca = "✅ " if proy in context.user_data["selected_projects"] else ""
            keyboard.append([InlineKeyboardButton(marca + proy, callback_data=proy)])
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])

        await query.edit_message_text(
            "📌 Seleccione los proyectos en los que participa:\n\n" +
            ", ".join(context.user_data["selected_projects"]) if context.user_data["selected_projects"] else "Ninguno aún",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECCION_PROYECTOS

async def rellenar_proyecto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de datos para cada proyecto seleccionado.
    """
    proyectos = context.user_data["selected_projects"]
    idx = context.user_data["current_project_index"]
    proyecto = proyectos[idx]

    # Inicializar estructura de datos para proyectos si no existe
    if "proyectos_data" not in context.user_data:
        context.user_data["proyectos_data"] = {}

    if proyecto not in context.user_data["proyectos_data"]:
        context.user_data["proyectos_data"][proyecto] = {}

    data_proy = context.user_data["proyectos_data"][proyecto]

    # Solicitar datos en secuencia: segmentos, manzanas, encuestas, semana
    if "SEGMENTOS" not in data_proy:
        data_proy["SEGMENTOS"] = update.message.text
        await update.message.reply_text("Ingrese MANZANAS TRABAJADAS:")
        return RELLENAR_PROYECTO

    elif "MANZANAS" not in data_proy:
        data_proy["MANZANAS"] = update.message.text
        await update.message.reply_text("Ingrese CANTIDAD DE ENCUESTAS:")
        return RELLENAR_PROYECTO

    elif "ENCUESTAS" not in data_proy:
        data_proy["ENCUESTAS"] = update.message.text
        await update.message.reply_text("Ingrese SEMANA:")
        return RELLENAR_PROYECTO

    elif "SEMANA" not in data_proy:
        data_proy["SEMANA"] = update.message.text

        # Pasar al siguiente proyecto o terminar
        idx += 1
        if idx < len(proyectos):
            context.user_data["current_project_index"] = idx
            await update.message.reply_text(
                f"✅ {proyecto} completado.\n\nAhora vamos con *{proyectos[idx]}*.\nIngrese SEGMENTOS TRABAJADOS:",
                parse_mode="Markdown"
            )
            return RELLENAR_PROYECTO
        else:
            # Todos los proyectos completados, pedir confirmación
            await update.message.reply_text(
                "✅ Todos los proyectos han sido llenados.\n\n¿Desea confirmar y enviar los datos? (si/no)"
            )
            return CONFIRMAR
        
async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la confirmación y envío final de datos a Google Sheets.
    """
    if update.message.text.lower() == "si":
        try:
            # Construir fila para Google Sheets y enviar
            row = _build_google_row(context)
            append_row(
                spreadsheet_id=GOOGLE_SPREADSHEET_ID,
                sheet_name=GOOGLE_SHEET_NAME,
                row_values=row,
            )
            await update.message.reply_text("📤 Datos enviados con éxito a Google Sheets.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error enviando a Google Sheets: {e}")
    else:
        await update.message.reply_text("❌ Proceso cancelado.")
    return ConversationHandler.END  # Terminar la conversación

def _build_google_row(context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    """
    Construye una fila con los datos del usuario en el formato esperado por Google Sheets.
    """
    user_data = context.user_data
    # Datos básicos (columnas B-J)
    base = [
        user_data.get("CORREO", ""),      # Columna B - CORREO ELECTRONICO
        user_data.get("ENTIDAD", ""),     # Columna C - ENTIDAD
        user_data.get("FECHA", ""),       # Columna D - FECHA
        user_data.get("SUB_REGION", ""),  # Columna E - SUB REGION OPERATIVA
        user_data.get("MUNICIPIO", ""),   # Columna F - MUNICIPIO
        user_data.get("PARROQUIA", ""),   # Columna G - PARROQUIA
        user_data.get("NODO", ""),        # Columna H - NODO
        user_data.get("CEDULA", ""),      # Columna I - CEDULA DE IDENTIDAD
        user_data.get("CARGO", ""),       # Columna J - CARGO
    ]

    proyectos_cols: List[str] = []
    selected: List[str] = user_data.get("selected_projects", [])
    data: dict = user_data.get("proyectos_data", {})

    # Para cada proyecto (1-9), agregar 4 columnas con sus datos o vacío
    for i in range(1, 10):
        nombre = f"Proyecto {i}"
        if nombre in selected and nombre in data:
            d = data.get(nombre, {})
            proyectos_cols.extend([
                d.get("SEGMENTOS", ""),  # Primera columna del proyecto
                d.get("MANZANAS", ""),   # Segunda columna del proyecto
                d.get("ENCUESTAS", ""),  # Tercera columna del proyecto
                d.get("SEMANA", ""),     # Cuarta columna del proyecto
            ])
        else:
            proyectos_cols.extend(["", "", "", ""])  # Vacíos si no participa

    return base + proyectos_cols  # Combinar datos básicos con datos de proyectos
# Manejador de conversación que agrupa todos los estados y handlers
def get_conv_handler() -> ConversationHandler:
    """
    Crea y configura el manejador de conversación con todos los estados y handlers.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],  # Comando que inicia la conversación
        states={
            # Asociar cada estado con su handler correspondiente
            ENTIDAD: [CallbackQueryHandler(entidad)],
            FECHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, fecha)],
            SUB_REGION: [CallbackQueryHandler(sub_region)],
            PARROQUIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, parroquia)],
            MUNICIPIO: [CallbackQueryHandler(municipio)],
            NODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nodo)],
            CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cedula)],
            CARGO: [CallbackQueryHandler(cargo)],
            CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, correo)],
            SELECCION_PROYECTOS: [CallbackQueryHandler(seleccionar_proyectos)],
            RELLENAR_PROYECTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, rellenar_proyecto)],
            CONFIRMAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],  # Comando para cancelar la conversación
        per_chat=True,    # Una conversación por chat
        per_user=True,    # Una conversación por usuario
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la cancelación de la conversación.
    """
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END  # Terminar la conversación