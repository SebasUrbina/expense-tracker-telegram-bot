import boto3
import json
import urllib3
import os
import re
from db.dynamo import DynamoTable
from sheets.google_sheets import GoogleSheets
import logging
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
SHEETS = {
    'YourTelegramUserName': 'YourGoogleSheetsSpreadsheetId'
}

# Configuración del logger al inicio del archivo
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def sendReply(chat_id, message, buttons=None, menu=None):

    # Construir el mensaje básico
    reply = {
        "chat_id": chat_id,
        "text": message
    }

    # Agregar botones interactivos en línea
    if buttons:
        reply["reply_markup"] = {
            "inline_keyboard": buttons
        }
    # Agregar menú con opciones preestablecidas
    elif menu:
        reply["reply_markup"] = {
            "keyboard": menu,
            "resize_keyboard": True,  # Ajusta el tamaño del teclado
            "one_time_keyboard": False  # El teclado no desaparece tras ser usado
        }

    http = urllib3.PoolManager()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    encoded_data = json.dumps(reply).encode('utf-8')
    http.request(
        'POST',
        url,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )

    logger.info(f"Reply: {encoded_data}")


def extract_cell_range(message: str):
    # Busca el texto que está después de "Celda: " hasta el final de la línea
    match = re.search(r'📊 Celda: ([A-Z0-9:]+)', message)
    if match:
        return match.group(1)
    return None


def deleteMessage(chat_id, message_id):
    """
    Elimina un mensaje específico del chat de Telegram

    Args:
        chat_id: ID del chat
        message_id: ID del mensaje a eliminar
    """
    delete_message = {
        "chat_id": chat_id,
        "message_id": message_id
    }

    http = urllib3.PoolManager()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
    encoded_data = json.dumps(delete_message).encode('utf-8')
    http.request(
        'POST',
        url,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )

    logger.info(
        f"Mensaje eliminado: chat_id={chat_id}, message_id={message_id}")


def lambda_handler(event, context):
    user_session_table = DynamoTable('TelegramBotUserSession')
    user_expenses_table = DynamoTable('TelegramBotUserExpenses')

    body = json.loads(event['body'])
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
        cell_range = extract_cell_range(message_text)
    else:
        key_date = "message" if "message" in body else "edited_message"
        chat_id = body[key_date]['chat']['id']
        user_name = body[key_date]['from']['username']
        message_text = body[key_date]['text']
        message_date = body[key_date]['date']
        inline_action = None

    logger.info("chat id: %s", chat_id)
    logger.info("user name: %s", user_name)
    logger.info("message text: %s", message_text)
    logger.info("message date: %s", message_date)
    logger.info("body: %s", json.dumps(body))

    # Init Google Sheets
    google_sheets = GoogleSheets(SHEETS[user_name])

    if inline_action == "delete_record" and cell_range:
        # Eliminar el registro de Google Sheets
        google_sheets.delete_expense(cell_range)

        # Eliminar el mensaje usando la nueva función
        message_id = body["callback_query"]["message"]["message_id"]
        deleteMessage(chat_id, message_id)

        return {
            'statusCode': 200,
            'body': json.dumps('Message processed successfully')
        }

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
        ["Sueldo"]
    ]

    # Variables para simular almacenamiento en base de datos
    if message_text.lower() == "/start":
        reply_message = f"Hola @{user_name}, selecciona una categoría:"
        sendReply(chat_id, reply_message, menu=CATEGORIES)

    elif message_text in [item for sublist in CATEGORIES for item in sublist]:
        # Guardar la categoría seleccionada temporalmente
        user_session_table.put_item(
            item={
                'chat_id': chat_id,
                'selected_category': message_text
            }
        )
        reply_message = f"✅ Has seleccionado la categoría: {message_text} 📂\n📝 Ahora envía un mensaje en el formato:\n📍 DD-MM descripción monto 💰"
        sendReply(chat_id, reply_message)

    else:
        # Procesar el mensaje en formato esperado
        match = re.match(r"(\d{1,2}-\d{1,2}) (.+) (\d+)", message_text)
        if match:
            date_str, description, amount = match.groups()
            # Agregar el año actual al formato dd-mm
            current_year = datetime.now().year
            date = f"{date_str}-{current_year}"

            category = user_session_table.get_value(
                chat_id, 'selected_category')

            if not category:
                sendReply(
                    chat_id, "Por favor selecciona una categoría antes de registrar un gasto.")

            # Guardar en Dynamo
            user_expenses_table.put_item(
                item={
                    'chat_id': chat_id,
                    'record_id': message_date,
                    'category': category,
                    'date': date,
                    'description': description,
                    'amount': amount
                }
            )

            # Escribir en Google Sheets
            updated_range = google_sheets.append_expenses([
                [date, description, category, amount]
            ])

            # save_expense(chat_id, message_date, description, amount, date, category)
            reply_message = (
                f"✅ Registro agregado exitosamente:\n"
                f"📂 Categoría: {category}\n"
                f"📅 Fecha: {date}\n"
                f"📝 Descripción: {description}\n"
                f"💰 Monto: ${amount}\n"
                f"📊 Celda: {updated_range}"
            )

            # Agregar botones para actualizar o eliminar
            buttons = [
                [{"text": "Eliminar", "callback_data": "delete_record"}]
            ]
            sendReply(chat_id, reply_message, buttons=buttons)
        else:
            reply_message = "Formato inválido. Por favor, envía un mensaje en el formato:\n- DD-MM descripción monto."
            sendReply(chat_id, reply_message)

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
