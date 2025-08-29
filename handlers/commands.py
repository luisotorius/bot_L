"""
MÓDULO DE COMANDOS PARA BOT DE TELEGRAM
Este módulo maneja la conversación con el usuario para recolectar datos
y enviarlos a Google Sheets. Utiliza el patrón ConversationHandler de python-telegram-bot.
"""

# Importaciones necesarias para el funcionamiento del bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from typing import List
from datetime import datetime  # Importamos datetime para las marcas temporales

# Importaciones propias de la aplicación
from utils.google_sheets import append_row  # Función para enviar datos a Google Sheets
from config import GOOGLE_SPREADSHEET_ID, GOOGLE_SHEET_NAME  # Configuración de la hoja de cálculo

# DEFINICIÓN DE ESTADOS DE LA CONVERSACIÓN - NUEVO ORDEN
(
    CEDULA,           # Paso 1: Cédula (Columna C)
    CORREO,           # Paso 2: Correo (Columna D)
    MUNICIPIO,        # Paso 3: Municipio (Columna E)
    PARROQUIA,        # Paso 4: Parroquia (Columna F)
    ENTIDAD,          # Paso 5: Estado (Columna G)
    NODO,             # Paso 6: Nodo (Columna H)
    CARGO,            # Paso 7: Cargo (Columna I)
    SELECCION_PROYECTOS,  # Paso 8: Selección de proyectos
    RELLENAR_PROYECTO,    # Paso 9: Rellenar datos de cada proyecto
    CONFIRMAR_PROYECTO,   # Paso 10: Confirmación de proyecto individual
    CONFIRMAR_ENVIO,      # Paso 11: Confirmación final y envío
) = range(11)  # Asigna números del 0 al 10 a cada estado

# OPCIONES PREESTABLECIDAS
ENTIDADES = ["ZULIA"]
MUNICIPIOS = [
  "ALMIRANTE PADILLA", "BARALT", "CABIMAS", "CATATUMBO", "COLON", 
  "FRANCISCO JAVIER PULGAR", "JESUS ENRIQUE LOSSADA", "JESUS MARIA SEMPRUN",
  "LA CAÑADA DE URDANETA", "LAGUNILLAS", "MACHIQUES DE PERIJA", "MARA",
  "MARACAIBO", "MIRANDA", "PAEZ", "ROSARIO DE PERIJA", "SAN FRANCISCO",
  "SANTA RITA", "SIMON BOLIVAR", "SUCRE", "VALMORES RODRIGUEZ"
]
CARGOS = [
  "COORDINADOR MUNICIPAL",
  "COORDINADOR NODO",
  "SUPERVISOR DE NODO",
  "VERIFICADOR ENCUESTADOR INTEGRAR"
]

# LISTA DE PROYECTOS DISPONIBLES
PROYECTOS = [
    "PROYECTO E.S.C.V. / ACTIVO", "BOLETA GRAN MISIÓN EQUIDAD Y JUSTICIA SOCIAL", "FLASH POS ELECTORAL / ACTIVO",
    "PROYECTO CANASTA TIPOLOGÍA ABASTOS Y BODEGAS 2025 / ACTIVO", "ENCUESTA INDUSTRIAL CUALITATIVA EN ÁMBITOS INDUSTRIALES - EN PLANIFICACIÓN /APENAS SE ACTIVE SE REPORTA LA INFORMACIÓN", "REGISTRO DE INFRAESTRUCTURAS EDUCATIVAS / ACTIVO",
    "ACTUALIZACIÓN DE LADO DE MANZANAS Y COMUNIDADES EN - EN PLANIFICACIÓN /APENAS SE ACTIVE SE REPORTA LA INFORMACIÓN", "CATASTRO", "INPC"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Función inicial que comienza la conversación.
    """
    context.user_data.clear()
    await update.message.reply_text("👋 Bienvenido.\n\n🪪 Ingrese la CÉDULA DE IDENTIDAD:")
    return CEDULA

async def cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de cédula (Columna C).
    """
    context.user_data["CEDULA"] = update.message.text
    await update.message.reply_text("📧 Ingrese su CORREO ELECTRÓNICO:")
    return CORREO

async def correo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de correo (Columna D).
    """
    context.user_data["CORREO"] = update.message.text
    
    # Preparar selección de municipio
    keyboard = [[InlineKeyboardButton(m, callback_data=m)] for m in MUNICIPIOS]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["MUNICIPIO"] = None
    await update.message.reply_text("🏙 Seleccione el MUNICIPIO:", reply_markup=reply_markup)
    return MUNICIPIO

async def municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de municipio (Columna E).
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

async def parroquia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de parroquia (Columna F).
    """
    context.user_data["PARROQUIA"] = update.message.text
    
    # Preparar selección de entidad (estado)
    keyboard = [[InlineKeyboardButton(ent, callback_data=ent)] for ent in ENTIDADES]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["ENTIDAD"] = None
    await update.message.reply_text("🏛 Seleccione la ENTIDAD/ESTADO:", reply_markup=reply_markup)
    return ENTIDAD

async def entidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de entidad/estado (Columna G).
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["ENTIDAD"]:
            await query.edit_message_text("⚠️ Debe seleccionar una ENTIDAD.")
            return ENTIDAD
        await query.edit_message_text(f"✅ ENTIDAD: {context.user_data['ENTIDAD']}\n\n🏘 Ingrese el NODO:")
        return NODO
    else:
        context.user_data["ENTIDAD"] = query.data
        keyboard = [[InlineKeyboardButton(ent, callback_data=ent)] for ent in ENTIDADES]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 ENTIDAD seleccionada: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ENTIDAD

async def nodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de nodo (Columna H).
    """
    context.user_data["NODO"] = update.message.text
    
    # Preparar selección de cargo
    keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in CARGOS]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["CARGO"] = None
    await update.message.reply_text("👔 Seleccione el CARGO:", reply_markup=reply_markup)
    return CARGO

async def cargo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de cargo (Columna I).
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["CARGO"]:
            await query.edit_message_text("⚠️ Debe seleccionar un CARGO.")
            return CARGO
        
        # Ir a selección de proyectos
        context.user_data["selected_projects"] = []
        keyboard = []
        for proy in PROYECTOS:
            keyboard.append([InlineKeyboardButton(proy, callback_data=proy)])
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            "✔️ Datos básicos completados.\n\n📌 Seleccione los proyectos en los que participa (puede elegir varios) y luego pulse ✅ Done.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SELECCION_PROYECTOS
    else:
        context.user_data["CARGO"] = query.data
        keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in CARGOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 CARGO seleccionado: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return CARGO

async def seleccionar_proyectos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección múltiple de proyectos."""
    query = update.callback_query
    await query.answer()
    seleccion = query.data

    if seleccion == "done":
        proyectos = context.user_data["selected_projects"]
        if not proyectos:
            await query.edit_message_text("⚠️ Debe seleccionar al menos un proyecto.")
            return SELECCION_PROYECTOS

        context.user_data["current_project_index"] = 0
        await query.edit_message_text(
            f"✍️ Vamos con *{proyectos[0]}*.\n\nIngrese la SEMANA:",
            parse_mode="Markdown"
        )
        return RELLENAR_PROYECTO
    else:
        if seleccion in context.user_data["selected_projects"]:
            context.user_data["selected_projects"].remove(seleccion)
        else:
            context.user_data["selected_projects"].append(seleccion)

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
    """Maneja el ingreso de datos para cada proyecto seleccionado."""
    proyectos = context.user_data["selected_projects"]
    idx = context.user_data["current_project_index"]
    proyecto = proyectos[idx]

    if "proyectos_data" not in context.user_data:
        context.user_data["proyectos_data"] = {}

    if proyecto not in context.user_data["proyectos_data"]:
        context.user_data["proyectos_data"][proyecto] = {}

    data_proy = context.user_data["proyectos_data"][proyecto]

    # Nuevo orden: Semana -> Segmentos -> Manzanas -> Encuestas
    if "SEMANA" not in data_proy:
        data_proy["SEMANA"] = update.message.text
        await update.message.reply_text("Ingrese los SEGMENTOS TRABAJADOS:")
        return RELLENAR_PROYECTO

    elif "SEGMENTOS" not in data_proy:
        data_proy["SEGMENTOS"] = update.message.text
        await update.message.reply_text("Ingrese las MANZANAS TRABAJADAS:")
        return RELLENAR_PROYECTO

    elif "MANZANAS" not in data_proy:
        data_proy["MANZANAS"] = update.message.text
        await update.message.reply_text("Ingrese la CANTIDAD DE ENCUESTAS:")
        return RELLENAR_PROYECTO

    elif "ENCUESTAS" not in data_proy:
        data_proy["ENCUESTAS"] = update.message.text
        
        # Mostrar resumen y pedir confirmación para este proyecto
        resumen = f"""
📋 *Resumen de {proyecto}:*
        
🗓 *Semana:* {data_proy['SEMANA']}
📍 *Segmentos:* {data_proy['SEGMENTOS']}
🏘 *Manzanas:* {data_proy['MANZANAS']}
📊 *Encuestas:* {data_proy['ENCUESTAS']}

¿Los datos son correctos? (si/no)
Si hay algún error, responde 'no' para volver a llenar este proyecto.
        """
        
        await update.message.reply_text(resumen, parse_mode="Markdown")
        return CONFIRMAR_PROYECTO

async def confirmar_proyecto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la confirmación o corrección de cada proyecto individual."""
    respuesta = update.message.text.lower()
    proyectos = context.user_data["selected_projects"]
    idx = context.user_data["current_project_index"]
    proyecto = proyectos[idx]
    
    if respuesta == 'si':
        # Proyecto confirmado, pasar al siguiente
        idx += 1
        if idx < len(proyectos):
            context.user_data["current_project_index"] = idx
            await update.message.reply_text(
                f"✅ *{proyecto}* confirmado.\n\nAhora vamos con *{proyectos[idx]}*.\nIngrese la SEMANA:",
                parse_mode="Markdown"
            )
            return RELLENAR_PROYECTO
        else:
            # Todos los proyectos completados y confirmados
            await mostrar_resumen_final(update, context)
            return CONFIRMAR_ENVIO
            
    elif respuesta == 'no':
        # Volver a llenar el mismo proyecto
        del context.user_data["proyectos_data"][proyecto]  # Eliminar datos incorrectos
        await update.message.reply_text(
            f"🔄 Vamos a corregir *{proyecto}*.\n\nIngrese la SEMANA:",
            parse_mode="Markdown"
        )
        return RELLENAR_PROYECTO
        
    else:
        await update.message.reply_text("❌ Por favor, responda 'si' o 'no'.")
        return CONFIRMAR_PROYECTO

async def mostrar_resumen_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra un resumen final de todos los datos antes del envío."""
    user_data = context.user_data
    proyectos_data = user_data.get("proyectos_data", {})
    
    resumen = "📋 *RESUMEN FINAL DE TODOS LOS DATOS*\n\n"
    
    # Datos básicos
    resumen += f"*👤 Datos Personales:*\n"
    resumen += f"🪪 Cédula: {user_data.get('CEDULA', '')}\n"
    resumen += f"📧 Correo: {user_data.get('CORREO', '')}\n"
    resumen += f"🏙 Municipio: {user_data.get('MUNICIPIO', '')}\n"
    resumen += f"🏘 Parroquia: {user_data.get('PARROQUIA', '')}\n"
    resumen += f"🏛 Estado: {user_data.get('ENTIDAD', '')}\n"
    resumen += f"📍 Nodo: {user_data.get('NODO', '')}\n"
    resumen += f"👔 Cargo: {user_data.get('CARGO', '')}\n\n"
    
    # Proyectos
    resumen += f"*📊 Proyectos seleccionados ({len(user_data.get('selected_projects', []))}):*\n"
    for proyecto in user_data.get("selected_projects", []):
        data = proyectos_data.get(proyecto, {})
        resumen += f"🔹 *{proyecto}:*\n"
        resumen += f"   🗓 Semana: {data.get('SEMANA', '')}\n"
        resumen += f"   📍 Segmentos: {data.get('SEGMENTOS', '')}\n"
        resumen += f"   🏘 Manzanas: {data.get('MANZANAS', '')}\n"
        resumen += f"   📊 Encuestas: {data.get('ENCUESTAS', '')}\n\n"
    
    resumen += "¿Desea confirmar y enviar TODOS los datos? (si/no)\n"
    resumen += "⚠️ *Una vez enviados, no podrán modificarse*"
    
    await update.message.reply_text(resumen, parse_mode="Markdown")

async def confirmar_envio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la confirmación final y envío de todos los datos."""
    if update.message.text.lower() == "si":
        try:
            row = _build_google_row(context)
            append_row(
                spreadsheet_id=GOOGLE_SPREADSHEET_ID,
                sheet_name=GOOGLE_SHEET_NAME,
                row_values=row,
            )
            await update.message.reply_text("✅ 📤 *Datos enviados con éxito a Google Sheets.*", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ *Error enviando a Google Sheets:* {e}", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Proceso cancelado. Los datos no fueron enviados.")
    
    return ConversationHandler.END

def _build_google_row(context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    """
    Construye una fila con los datos del usuario en el nuevo formato para Google Sheets.
    """
    user_data = context.user_data
    now = datetime.now()
    
    # Datos automáticos (columnas A-B)
    automaticos = [
        now.strftime("%Y-%m-%d %H:%M:%S"),  # Columna A - Marca temporal
        now.strftime("%Y-%m-%d"),           # Columna B - Fecha de levantamiento
    ]
    
    # Datos básicos del usuario (columnas C-I) - Mismo orden que la conversación
    basicos = [
        user_data.get("CEDULA", ""),        # Columna C - CÉDULA DE IDENTIDAD
        user_data.get("CORREO", ""),        # Columna D - CORREO ELECTRONICO
        user_data.get("MUNICIPIO", ""),     # Columna E - MUNICIPIO
        user_data.get("PARROQUIA", ""),     # Columna F - PARROQUIA
        user_data.get("ENTIDAD", ""),       # Columna G - ESTADO
        user_data.get("NODO", ""),          # Columna H - NODO
        user_data.get("CARGO", ""),         # Columna I - CARGO
    ]
    
    # Datos de proyectos (columnas J-AS)
    proyectos_cols: List[str] = []
    selected: List[str] = user_data.get("selected_projects", [])
    data: dict = user_data.get("proyectos_data", {})
    
    for i in range(1, 10):
        nombre = f"Proyecto {i}"
        if nombre in selected and nombre in data:
            d = data.get(nombre, {})
            proyectos_cols.extend([
                d.get("SEMANA", ""),        # Semana
                d.get("SEGMENTOS", ""),     # Segmentos trabajados
                d.get("MANZANAS", ""),      # Manzanas trabajadas
                d.get("ENCUESTAS", ""),     # Cantidad de encuestas
            ])
        else:
            proyectos_cols.extend(["", "", "", ""])

    return automaticos + basicos + proyectos_cols

# Manejador de conversación que agrupa todos los estados y handlers
def get_conv_handler() -> ConversationHandler:
    """
    Crea y configura el manejador de conversación con todos los estados и handlers.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # Nuevo orden de estados según las columnas
            CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cedula)],
            CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, correo)],
            MUNICIPIO: [CallbackQueryHandler(municipio)],
            PARROQUIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, parroquia)],
            ENTIDAD: [CallbackQueryHandler(entidad)],
            NODO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nodo)],
            CARGO: [CallbackQueryHandler(cargo)],
            SELECCION_PROYECTOS: [CallbackQueryHandler(seleccionar_proyectos)],
            RELLENAR_PROYECTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, rellenar_proyecto)],
            CONFIRMAR_PROYECTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_proyecto)],
            CONFIRMAR_ENVIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmar_envio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_chat=True,
        per_user=True,
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la cancelación de la conversación."""
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END
    """
    Maneja la cancelación de la conversación.
    """
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END  # Terminar la conversación