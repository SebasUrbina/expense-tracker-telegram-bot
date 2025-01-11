import json
import os
import re
from db.dynamo import DynamoTable
from sheets.google_sheets import GoogleSheets
from telegram.telegram_api import TelegramAPI
from utils.utils import (
    extract_cell_range_from_message,
    setup_logger,
    is_google_sheet_url,
    extract_sheet_id_from_message,
    extract_data_from_message,
)
from datetime import datetime

# Configuración del logger al inicio del archivo
logger = setup_logger(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GCP_MAIL_EDITOR = os.environ["GCP_MAIL_EDITOR"]


def lambda_handler(event, context):

    # Init classes
    user_session_table = DynamoTable("TelegramBotUserSession")
    user_expenses_table = DynamoTable("TelegramBotUserExpenses")
    telegram_api = TelegramAPI(BOT_TOKEN)

    # Get body from event
    body = json.loads(event["body"])
    logger.info("EventBody: %s", body)

    logger.info("Received event")

    # Get metadata from message
    if "callback_query" in body:
        key_date = "callback_query"
        chat_id = body[key_date]["message"]["chat"]["id"]
        user_name = body[key_date]["message"]["chat"]["username"]
        message_text = body[key_date]["message"]["text"]
        message_date = body[key_date]["message"]["date"]
        inline_action = body[key_date]["data"]
        cell_range = extract_cell_range_from_message(message_text)

    else:
        key_date = "message" if "message" in body else "edited_message"
        chat_id = body[key_date]["chat"]["id"]
        user_name = body[key_date]["from"]["username"]
        message_text = body[key_date]["text"]
        message_date = body[key_date]["date"]
        inline_action = None

    logger.info("chat id: %s", chat_id)
    logger.info("user name: %s", user_name)
    logger.info("message text: %s", message_text)
    logger.info("message date: %s", message_date)
    logger.info("body: %s", json.dumps(body))

    # Init Google Sheets
    try:
        sheet_id = user_session_table.get_value(chat_id, "sheet_id")
        logger.info(f"Sheet ID: {sheet_id}")
        google_sheets = GoogleSheets(sheet_id)
    except Exception as e:
        logger.info(f"Error initializing Google Sheets: {e}")
        pass

    if inline_action == "delete_record" and cell_range:

        # Eliminar el registro de Google Sheets
        google_sheets.delete_expense(cell_range)

        # Eliminar el mensaje en el chat de telegram
        message_id = body["callback_query"]["message"]["message_id"]
        telegram_api.delete_message(chat_id, message_id)

        # Eliminar el registro de DynamoDB
        data = extract_data_from_message(message_text)
        user_expenses_table.delete_item_by_conditions(chat_id, data)

        return {"statusCode": 200, "body": json.dumps("Message processed successfully")}

    # Categorías predefinidas
    CATEGORIES = [
        ["Supermercado", "Almuerzo", "Transporte"],
        ["Metro", "Recreacional", "Ingreso"],
        ["Farmacia", "Ropa", "Vacaciones"],
        ["Apps", "Eventos", "Electronica"],
        ["Otros", "Familia", "Regalos"],
        ["Fintual", "Criptomonedas", "Comision BC"],
        ["Arriendo", "Gasto Común", "Agua"],
        ["Luz", "Internet", "Pension"],
        ["Sueldo"],
    ]

    # Variables para simular almacenamiento en base de datos
    if message_text.lower() == "/start":
        # Validar si existe un SheetID en user_session_table
        sheet_id = user_session_table.get_value(chat_id, "sheet_id")
        if not sheet_id:
            reply_message = (
                f"📝 Ingresa la URL de tu Google Sheet para registrar tus gastos"
            )
            reply_message += f"\n\n📧 Debes compartir el Google Sheet con el correo: {GCP_MAIL_EDITOR}"
            telegram_api.send_reply(chat_id, reply_message)
        else:
            reply_message = f"Hola @{user_name}, selecciona una categoría:"
            telegram_api.send_reply(chat_id, reply_message)

    # Si envia una URL de Google Sheet, extrae el ID y lo guarda en user_session_table
    elif is_google_sheet_url(message_text):
        sheet_id = extract_sheet_id_from_message(message_text)
        if sheet_id:
            user_session_table.put_item(
                item={
                    "chat_id": chat_id,
                    "sheet_id": sheet_id,
                    "selected_category": None,
                }
            )
            reply_message = f"✅ Google Sheet ID guardado correctamente. Ya puedes registrar tus gastos, selecciona una categoría:"
            telegram_api.send_reply(chat_id, reply_message)
        else:
            reply_message = f"Error al guardar el Google Sheet ID"
            telegram_api.send_reply(chat_id, reply_message)

    elif message_text in [item for sublist in CATEGORIES for item in sublist]:
        # Guardar la categoría seleccionada temporalmente
        user_session_table.update_item(chat_id, "selected_category", message_text)

        reply_message = f"✅ Has seleccionado la categoría: {message_text} 📂\n📝 Ahora envía un mensaje en el formato:\n📍 DD-MM descripción monto 💰"
        telegram_api.send_reply(chat_id, reply_message)

    else:
        # Primero intentar con formato fecha + descripción + monto
        match_with_date = re.match(r"(\d{1,2}-\d{1,2}) (.+) (\d+)", message_text)

        # Luego intentar solo descripción + monto
        match_without_date = re.match(r"(.+) (\d+)", message_text)

        # Si no coincide con ningún formato, mostrar error
        if not match_with_date and not match_without_date:
            telegram_api.send_reply(
                chat_id,
                "❌ Formato inválido. Por favor, envía un mensaje en el formato:\n📝 DD-MM descripción monto\n✨ O simplemente: descripción monto",
            )
            return

        # Obtener los datos según el formato que coincidió
        if match_with_date:
            dd_mm, description, amount = match_with_date.groups()
            yyyy = datetime.now().year
            date = f"{dd_mm}-{yyyy}"
        else:
            description, amount = match_without_date.groups()
            date = datetime.now().strftime("%d-%m-%Y")

        # Verificar que haya una categoría seleccionada
        category = user_session_table.get_value(chat_id, "selected_category")
        if not category:
            telegram_api.send_reply(
                chat_id,
                "❗ Por favor selecciona una categoría antes de registrar un gasto. 📝",
            )
            return

        # Guardar en DynamoDB
        user_expenses_table.put_item(
            item={
                "chat_id": chat_id,
                "user_name": user_name,
                "record_id": message_date,
                "category": category,
                "date": date,
                "description": description,
                "amount": amount,
            }
        )

        # Guardar en Google Sheets
        updated_range = google_sheets.append_expenses(
            [[date, description, category, amount]]
        )

        # Enviar mensaje de confirmación
        reply_message = (
            f"✅ Registro agregado exitosamente:\n"
            f"📂 Categoría: {category}\n"
            f"📅 Fecha: {date}\n"
            f"📝 Descripción: {description}\n"
            f"💰 Monto: ${amount}\n"
            f"📊 Celda: {updated_range}"
        )

        # Agregar botón para eliminar
        buttons = [[{"text": "Eliminar", "callback_data": "delete_record"}]]
        telegram_api.send_reply(chat_id, reply_message, buttons=buttons)

    return {"statusCode": 200, "body": json.dumps("Message processed successfully")}
