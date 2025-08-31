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
    FECHA_LEVANTAMIENTO,  # Paso 1: Fecha del levantamiento (Columna B)
    CEDULA,               # Paso 2: Cédula (Columna C)
    CORREO,               # Paso 3: Correo (Columna D)
    NODO,                 # Paso 4: Nodo (Columna E)
    ESTADO,               # Paso 5: Estado (Columna F)
    MUNICIPIO,            # Paso 6: Municipio (Columna G)
    PARROQUIA,            # Paso 7: Parroquia (Columna H)
    CARGO,                # Paso 8: Cargo (Columna I)
    SELECCION_PROYECTOS,  # Paso 9: Selección de proyectos
    RELLENAR_PROYECTO,    # Paso 10: Rellenar datos de cada proyecto
    CONFIRMAR_PROYECTO,   # Paso 11: Confirmación de proyecto individual
    CONFIRMAR_ENVIO,      # Paso 12: Confirmación final y envío
) = range(12)  # Asigna números del 0 al 11 a cada estado

# OPCIONES PREESTABLECIDAS
ESTADOS = ["ZULIA"]

# MUNICIPIOS Y SUS PARROQUIAS CORRESPONDIENTES
MUNICIPIOS_PARROQUIAS = {
    "ALMIRANTE PADILLA": ["Isla de Toas", "Monagas"],
    "BARALT": ["San Timoteo", "General Urdaneta", "Libertador", "Manuel Guanipa Matos", "Rómulo Betancourt", "Pueblo Nuevo"],
    "CABIMAS": ["Ambrosio", "Carmen Herrera", "Germán Ríos Linares", "La Rosa", "Jorge Hernández", "Rómulo Betancourt", "San Benito", "Arístides Calvani", "Punta Gorda"],
    "CATATUMBO": ["Encontrados", "Udón Pérez"],
    "COLON": ["San Carlos del Zulia", "Moralito", "Santa Bárbara", "Santa Cruz del Zulia", "Urribarrí"],
    "FRANCISCO JAVIER PULGAR": ["Simón Rodríguez", "Carlos Quevedo", "Francisco Javier Pulgar", "Agustín Codazzi"],
    "JESUS ENRIQUE LOSSADA": ["La Concepción", "José Ramón Yépez", "Mariano Parra León", "San José"],
    "JESUS MARIA SEMPRUN": ["Jesús María Semprún", "Barí"],
    "LA CAÑADA DE URDANETA": ["Concepción", "Andrés Bello", "Chiquinquirá", "El Carmelo", "Potreritos"],
    "LAGUNILLAS": ["Alonso de Ojeda", "Libertad", "Campo Lara", "Eleazar López Contreras", "Venezuela", "El Danto"],
    "MACHIQUES DE PERIJA": ["Libertad", "Bartolomé de las Casas", "Río Negro", "San José de Perijá"],
    "MARA": ["San Rafael", "La Sierrita", "Las Parcelas", "Luis de Vicente", "Monseñor Marcos Sergio Godoy", "Ricaurte", "Tamare"],
    "MARACAIBO": ["Antonio Borjas Romero", "Bolívar", "Cacique Mara", "Caracciolo Parra Pérez", "Cecilio Acosta", "Cristo de Aranza", "Coquivacoa", "Chiquinquirá", "Francisco Eugenio Bustamante", "Idelfonso Vásquez", "Juana de Ávila", "Luis Hurtado Higuera", "Manuel Dagnino", "Olegario Villalobos", "Raúl Leoni", "Santa Lucía", "Venancio Pulgar", "San Isidro"],
    "MIRANDA": ["Altagracia", "Ana María Campos", "Faría", "San Antonio", "San José", "José Antonio Chávez"],
    "GOAJIRA": ["Sinamaica", "Alta Guajira", "Elías Sánchez Rubio", "Guajira"],
    "ROSARIO DE PERIJA": ["El Rosario", "Donaldo García", "Sixto Zambrano"],
    "SAN FRANCISCO": ["San Francisco", "El Bajo", "Domitila Flores", "Francisco Ochoa", "Los Cortijos", "Marcial Hernández", "José Domingo Rus"],
    "SANTA RITA": ["Santa Rita", "El Mene", "José Cenobio Urribarrí", "Pedro Lucas Urribarrí"],
    "SIMON BOLIVAR": ["Manuel Manrique", "Rafael María Baralt", "Rafael Urdaneta"],
    "SUCRE": ["Bobures", "El Batey", "Gibraltar", "Heras", "Monseñor Arturo Celestino Álvarez", "Rómulo Gallegos"],
    "VALMORES RODRIGUEZ": ["La Victoria", "Rafael Urdaneta", "Raúl Cuenca"]
}

# Lista de municipios para mostrar en botones
MUNICIPIOS = list(MUNICIPIOS_PARROQUIAS.keys())

# CARGOS CON IDENTIFICADORES ÚNICOS
CARGOS = [
    "COORDINADOR MUNICIPAL",
    "COORDINADOR DE NODO",
    "SUPERVISOR DE NODO",
    "VERIFICADOR ENCUESTADOR INTEGRAR"
]

# Mapeo de cargos para mostrar nombres completos
CARGOS_DISPLAY = {
    "COORDINADOR MUNICIPAL": "COORDINADOR MUNICIPAL",
    "COORDINADOR DE NODO": "COORDINADOR DE NODO", 
    "SUPERVISOR DE NODO": "SUPERVISOR DE NODO",
    "VERIFICADOR ENCUESTADOR INTEGRAR": "VERIFICADOR ENCUESTADOR INTEGRAR"
}

# LISTA DE PROYECTOS REALES SEGÚN ARCHIVO (CON IDENTIFICADORES ÚNICOS)
PROYECTOS = [
    "ESC_V",
    "BOLETA_GM",
    "FLASH_POS",
    "CANASTA_TIPOLOGIA",
    "ENCUESTA_INDUSTRIAL",
    "REGISTRO_EDUCATIVAS",
    "ACTUALIZACION_MANZANAS",
    "CATASTRO",
    "INPC"
]

# Mapeo de proyectos para mostrar nombres completos
PROYECTOS_DISPLAY = {
    "ESC_V": "PROYECTO E.S.C.V. / ACTIVO",
    "BOLETA_GM": "PROYECTO BOLETA GRAN MISIÓN EQUIDAD Y JUSTICIA SOCIAL",
    "FLASH_POS": "PROYECTO FLASH POS ELECTORAL / ACTIVO",
    "CANASTA_TIPOLOGIA": "PROYECTO CANASTA TIPOLOGÍA ABASTOS Y BODEGAS 2025 / ACTIVO",
    "ENCUESTA_INDUSTRIAL": "PROYECTO ENCUESTA INDUSTRIAL CUALITATIVA EN ÁMBITOS INDUSTRIALES - EN PLANIFICACIÓN",
    "REGISTRO_EDUCATIVAS": "PROYECTO REGISTRO DE INFRAESTRUCTURAS EDUCATIVAS / ACTIVO",
    "ACTUALIZACION_MANZANAS": "PROYECTO ACTUALIZACIÓN DE LADO DE MANZANAS Y COMUNIDADES - EN PLANIFICACIÓN",
    "CATASTRO": "PROYECTO CATASTRO",
    "INPC": "PROYECTO INPC"
}

# Mapeo de columnas para cada proyecto en Google Sheets
PROYECTOS_COLUMNAS = {
    "ESC_V": ["J", "K", "L"],  # Segmentos, Manzanas, Encuestas
    "BOLETA_GM": ["M", "N", "O"],  # Segmentos, Manzanas, Encuestas
    "FLASH_POS": ["P", "Q", "R"],  # Segmentos, Manzanas, Encuestas
    "CANASTA_TIPOLOGIA": ["S", "T", "U", "V"],  # Semana, Segmentos, Manzanas, Encuestas
    "ENCUESTA_INDUSTRIAL": ["W", "X", "Y"],  # Segmentos, Manzanas, Encuestas
    "REGISTRO_EDUCATIVAS": ["Z", "AA", "AB"],  # Segmentos, Manzanas, Encuestas
    "ACTUALIZACION_MANZANAS": ["AC", "AD", "AE"],  # Segmentos, Manzanas, Encuestas
    "CATASTRO": ["AF", "AG", "AH"],  # Segmentos, Manzanas, Encuestas
    "INPC": ["AI", "AJ", "AK", "AL"]  # Semana, Segmentos, Manzanas, Encuestas
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Función inicial que comienza la conversación.
    """
    context.user_data.clear()
    await update.message.reply_text("👋 Bienvenido.\n\n📅 Ingrese la FECHA DEL LEVANTAMIENTO (formato: YYYY-MM-DD):")
    return FECHA_LEVANTAMIENTO

async def fecha_levantamiento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de la fecha del levantamiento (Columna B).
    """
    fecha = update.message.text
    # Validar formato de fecha
    try:
        datetime.strptime(fecha, "%Y-%m-%d")
        context.user_data["FECHA_LEVANTAMIENTO"] = fecha
        await update.message.reply_text("🪪 Ingrese la CÉDULA DE IDENTIDAD:")
        return CEDULA
    except ValueError:
        await update.message.reply_text("❌ Formato de fecha incorrecto. Use YYYY-MM-DD (ej: 2024-01-15):")
        return FECHA_LEVANTAMIENTO

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
    await update.message.reply_text("📍 Ingrese el NODO:")
    return NODO

async def municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de municipio (Columna G).
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["MUNICIPIO"]:
            await query.edit_message_text("⚠️ Debe seleccionar un MUNICIPIO.")
            return MUNICIPIO
        
        # Obtener parroquias del municipio seleccionado
        municipio_seleccionado = context.user_data["MUNICIPIO"]
        parroquias = MUNICIPIOS_PARROQUIAS.get(municipio_seleccionado, [])
        
        # Preparar selección de parroquia
        keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in parroquias]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["PARROQUIA"] = None
        await query.edit_message_text(f"✅ MUNICIPIO: {municipio_seleccionado}\n\n🏘 Seleccione la PARROQUIA:", reply_markup=reply_markup)
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
    Maneja la selección de parroquia (Columna H).
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["PARROQUIA"]:
            await query.edit_message_text("⚠️ Debe seleccionar una PARROQUIA.")
            return PARROQUIA
        
        # Preparar selección de cargo
        keyboard = []
        for cargo_id in CARGOS:
            keyboard.append([InlineKeyboardButton(CARGOS_DISPLAY[cargo_id], callback_data=cargo_id)])
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["CARGO"] = None
        await query.edit_message_text(f"✅ PARROQUIA: {context.user_data['PARROQUIA']}\n\n👔 Seleccione el CARGO:", reply_markup=reply_markup)
        return CARGO
    else:
        context.user_data["PARROQUIA"] = query.data
        # Obtener parroquias del municipio seleccionado para mostrar el teclado actualizado
        municipio_seleccionado = context.user_data["MUNICIPIO"]
        parroquias = MUNICIPIOS_PARROQUIAS.get(municipio_seleccionado, [])
        
        keyboard = [[InlineKeyboardButton(p, callback_data=p)] for p in parroquias]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 PARROQUIA seleccionada: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return PARROQUIA

async def estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección de entidad/estado (Columna F).
    """
    query = update.callback_query
    await query.answer()

    if query.data == "done":
        if not context.user_data["ESTADO"]:
            await query.edit_message_text("⚠️ Debe seleccionar una ENTIDAD.")
            return ESTADO
        
        # Preparar selección de municipio
        keyboard = [[InlineKeyboardButton(m, callback_data=m)] for m in MUNICIPIOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data["MUNICIPIO"] = None
        await query.edit_message_text(f"✅ ENTIDAD: {context.user_data['ESTADO']}\n\n🏙 Seleccione el MUNICIPIO:", reply_markup=reply_markup)
        return MUNICIPIO
    else:
        context.user_data["ESTADO"] = query.data
        keyboard = [[InlineKeyboardButton(est, callback_data=est)] for est in ESTADOS]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            f"👉 ENTIDAD seleccionada: {query.data}\nPresione ✅ Done para continuar.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return ESTADO

async def nodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el ingreso de nodo (Columna E).
    """
    context.user_data["NODO"] = update.message.text
    
    # Preparar selección de estado
    keyboard = [[InlineKeyboardButton(est, callback_data=est)] for est in ESTADOS]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.user_data["ESTADO"] = None
    await update.message.reply_text("🏛 Seleccione la ENTIDAD/ESTADO:", reply_markup=reply_markup)
    return ESTADO

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
            keyboard.append([InlineKeyboardButton(PROYECTOS_DISPLAY[proy], callback_data=proy)])
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        await query.edit_message_text(
            "✔️ Datos básicos completados.\n\n📌 Seleccione los proyectos en los que participa (puede elegir varios) y luego pulse ✅ Done.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return SELECCION_PROYECTOS
    else:
        # Guardar el cargo seleccionado usando el mapeo de display
        cargo_seleccionado = CARGOS_DISPLAY.get(query.data, query.data)
        context.user_data["CARGO"] = cargo_seleccionado
        
        # Crear teclado actualizado
        keyboard = []
        for cargo_id in CARGOS:
            # Marcar el cargo seleccionado
            if cargo_id == query.data:
                keyboard.append([InlineKeyboardButton(f"✅ {CARGOS_DISPLAY[cargo_id]}", callback_data=cargo_id)])
            else:
                keyboard.append([InlineKeyboardButton(CARGOS_DISPLAY[cargo_id], callback_data=cargo_id)])
        
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="done")])
        
        await query.edit_message_text(
            f"👉 CARGO seleccionado: {cargo_seleccionado}\nPresione ✅ Done para continuar.",
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
        primer_proyecto = proyectos[0]
        
        # Determinar si el primer proyecto tiene semana
        columnas = PROYECTOS_COLUMNAS.get(primer_proyecto, [])
        tiene_semana = len(columnas) == 4
        
        if tiene_semana:
            await query.edit_message_text(
                f"✍️ Vamos con *{PROYECTOS_DISPLAY[primer_proyecto]}*.\n\nIngrese la SEMANA:",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                f"✍️ Vamos con *{PROYECTOS_DISPLAY[primer_proyecto]}*.\n\nIngrese los SEGMENTOS TRABAJADOS:",
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
            keyboard.append([InlineKeyboardButton(marca + PROYECTOS_DISPLAY[proy], callback_data=proy)])
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
    
    # Obtener el mapeo de columnas para este proyecto
    columnas = PROYECTOS_COLUMNAS.get(proyecto, [])
    
    # Determinar qué campos necesita este proyecto
    tiene_semana = len(columnas) == 4  # Los proyectos con 4 columnas incluyen semana
    
    if tiene_semana:
        # Proyectos que incluyen semana: Semana -> Segmentos -> Manzanas -> Encuestas
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
    else:
        # Proyectos sin semana: Segmentos -> Manzanas -> Encuestas
        if "SEGMENTOS" not in data_proy:
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
    if tiene_semana:
        resumen = f"""
📋 *Resumen de {PROYECTOS_DISPLAY[proyecto]}:*
        
🗓 *Semana:* {data_proy.get('SEMANA', '')}
📍 *Segmentos:* {data_proy.get('SEGMENTOS', '')}
🏘 *Manzanas:* {data_proy.get('MANZANAS', '')}
📊 *Encuestas:* {data_proy.get('ENCUESTAS', '')}

¿Los datos son correctos? (si/no)
Si hay algún error, responde 'no' para volver a llenar este proyecto.
        """
    else:
        resumen = f"""
📋 *Resumen de {PROYECTOS_DISPLAY[proyecto]}:*
        
📍 *Segmentos:* {data_proy.get('SEGMENTOS', '')}
🏘 *Manzanas:* {data_proy.get('MANZANAS', '')}
📊 *Encuestas:* {data_proy.get('ENCUESTAS', '')}

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
            siguiente_proyecto = proyectos[idx]
            
            # Determinar si el siguiente proyecto tiene semana
            columnas = PROYECTOS_COLUMNAS.get(siguiente_proyecto, [])
            tiene_semana = len(columnas) == 4
            
            if tiene_semana:
                await update.message.reply_text(
                    f"✅ *{PROYECTOS_DISPLAY[proyecto]}* confirmado.\n\nAhora vamos con *{PROYECTOS_DISPLAY[siguiente_proyecto]}*.\nIngrese la SEMANA:",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"✅ *{PROYECTOS_DISPLAY[proyecto]}* confirmado.\n\nAhora vamos con *{PROYECTOS_DISPLAY[siguiente_proyecto]}*.\nIngrese los SEGMENTOS TRABAJADOS:",
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
        
        # Determinar si este proyecto tiene semana
        columnas = PROYECTOS_COLUMNAS.get(proyecto, [])
        tiene_semana = len(columnas) == 4
        
        if tiene_semana:
            await update.message.reply_text(
                f"🔄 Vamos a corregir *{PROYECTOS_DISPLAY[proyecto]}*.\n\nIngrese la SEMANA:",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"🔄 Vamos a corregir *{PROYECTOS_DISPLAY[proyecto]}*.\n\nIngrese los SEGMENTOS TRABAJADOS:",
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
    resumen += f"*📅 Fecha de Levantamiento:* {user_data.get('FECHA_LEVANTAMIENTO', '')}\n"
    resumen += f"*👤 Datos Personales:*\n"
    resumen += f"🪪 Cédula: {user_data.get('CEDULA', '')}\n"
    resumen += f"📧 Correo: {user_data.get('CORREO', '')}\n"
    resumen += f"📍 Nodo: {user_data.get('NODO', '')}\n"
    resumen += f"🏛 Estado: {user_data.get('ESTADO', '')}\n"
    resumen += f"🏙 Municipio: {user_data.get('MUNICIPIO', '')}\n"
    resumen += f"🏘 Parroquia: {user_data.get('PARROQUIA', '')}\n"
    resumen += f"👔 Cargo: {user_data.get('CARGO', '')}\n\n"
    
    # Proyectos
    resumen += f"*📊 Proyectos seleccionados ({len(user_data.get('selected_projects', []))}):*\n"
    for proyecto in user_data.get("selected_projects", []):
        data = proyectos_data.get(proyecto, {})
        resumen += f"🔹 *{PROYECTOS_DISPLAY[proyecto]}:*\n"
        
        # Determinar si el proyecto tiene semana
        columnas = PROYECTOS_COLUMNAS.get(proyecto, [])
        tiene_semana = len(columnas) == 4
        
        if tiene_semana:
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
            # Limpiar el mensaje de error para evitar problemas de formato
            error_msg = str(e)
            # Remover caracteres problemáticos para Markdown
            error_msg = error_msg.replace('*', '').replace('_', '').replace('`', '').replace('[', '').replace(']', '')
            # Limitar la longitud del mensaje
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            
            await update.message.reply_text(f"❌ *Error enviando a Google Sheets:*\n`{error_msg}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Proceso cancelado. Los datos no fueron enviados.")
    
    return ConversationHandler.END

def _build_google_row(context: ContextTypes.DEFAULT_TYPE) -> List[str]:
    """
    Construye una fila con los datos del usuario en el nuevo formato para Google Sheets.
    """
    user_data = context.user_data
    now = datetime.now()
    
    # Datos automáticos (columna A)
    automaticos = [
        now.strftime("%Y-%m-%d %H:%M:%S"),  # Columna A - Marca temporal
    ]
    
    # Fecha del levantamiento (columna B)
    fecha_levantamiento = [
        user_data.get("FECHA_LEVANTAMIENTO", ""),  # Columna B - Fecha de levantamiento
    ]
    
    # Datos básicos del usuario (columnas C-I)
    basicos = [
        user_data.get("CEDULA", ""),        # Columna C - CÉDULA DE IDENTIDAD
        user_data.get("CORREO", ""),        # Columna D - CORREO ELECTRONICO
        user_data.get("NODO", ""),          # Columna E - NODO
        user_data.get("ESTADO", ""),        # Columna F - ESTADO
        user_data.get("MUNICIPIO", ""),     # Columna G - MUNICIPIO
        user_data.get("PARROQUIA", ""),     # Columna H - PARROQUIA
        user_data.get("CARGO", ""),         # Columna I - CARGO
    ]
    
    # Datos de proyectos (columnas J-AL)
    proyectos_cols: List[str] = []
    selected: List[str] = user_data.get("selected_projects", [])
    data: dict = user_data.get("proyectos_data", {})
    
    # Crear un diccionario con todos los proyectos y sus datos
    todos_proyectos = {
        "ESC_V": ["", "", ""],  # J, K, L
        "BOLETA_GM": ["", "", ""],  # M, N, O
        "FLASH_POS": ["", "", ""],  # P, Q, R
        "CANASTA_TIPOLOGIA": ["", "", "", ""],  # S, T, U, V
        "ENCUESTA_INDUSTRIAL": ["", "", ""],  # W, X, Y
        "REGISTRO_EDUCATIVAS": ["", "", ""],  # Z, AA, AB
        "ACTUALIZACION_MANZANAS": ["", "", ""],  # AC, AD, AE
        "CATASTRO": ["", "", ""],  # AF, AG, AH
        "INPC": ["", "", "", ""]  # AI, AJ, AK, AL
    }
    
    # Llenar los datos de los proyectos seleccionados
    for proyecto in selected:
        if proyecto in data and proyecto in todos_proyectos:
            proyecto_data = data[proyecto]
            columnas = PROYECTOS_COLUMNAS.get(proyecto, [])
            
            if len(columnas) == 4:  # Proyecto con semana
                todos_proyectos[proyecto] = [
                    proyecto_data.get("SEMANA", ""),        # Semana
                    proyecto_data.get("SEGMENTOS", ""),     # Segmentos trabajados
                    proyecto_data.get("MANZANAS", ""),      # Manzanas trabajadas
                    proyecto_data.get("ENCUESTAS", "")      # Cantidad de encuestas
                ]
            else:  # Proyecto sin semana
                todos_proyectos[proyecto] = [
                    proyecto_data.get("SEGMENTOS", ""),     # Segmentos trabajados
                    proyecto_data.get("MANZANAS", ""),      # Manzanas trabajadas
                    proyecto_data.get("ENCUESTAS", "")      # Cantidad de encuestas
                ]
    
    # Convertir el diccionario a una lista plana en el orden correcto
    for proyecto in todos_proyectos.values():
        proyectos_cols.extend(proyecto)

    return automaticos + fecha_levantamiento + basicos + proyectos_cols

# Manejador de conversación que agrupa todos los estados y handlers
def get_conv_handler() -> ConversationHandler:
    """
    Crea y configura el manejador de conversación con todos los estados y handlers.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FECHA_LEVANTAMIENTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, fecha_levantamiento)],
            CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cedula)],
            CORREO: [MessageHandler(filters.TEXT & ~filters.COMMAND, correo)],
            MUNICIPIO: [CallbackQueryHandler(municipio)],
            PARROQUIA: [CallbackQueryHandler(parroquia)],
            ESTADO: [CallbackQueryHandler(estado)],
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