import boto3
from botocore.exceptions import ClientError
from utils.utils import setup_logger

logger = setup_logger(__name__)


class DynamoTable:
    dynamodb = boto3.resource("dynamodb")

    def __init__(self, table: str):
        self.name = table
        self.table = self.dynamodb.Table(table)

    def put_item(self, item: dict) -> None:
        """
        Inserta un elemento en la tabla DynamoDB.
        """
        try:
            self.table.put_item(Item=item)
        except ClientError as e:
            logger.error(f"Error saving item in {self.name}: {e}")

    def update_item(self, chat_id: int, column: str, value: str) -> None:
        """
        Actualiza un valor de una columna específica para un `chat_id` dado.
        """
        try:
            self.table.update_item(
                Key={"chat_id": chat_id},
                UpdateExpression=f"set {column} = :val",
                ExpressionAttributeValues={":val": value},
            )
        except ClientError as e:
            logger.error(f"Error updating item in {self.name}: {e}")

    def delete_item_by_conditions(self, chat_id: int, conditions: dict) -> None:
        """
        Elimina un ítem basado en el `chat_id` y condiciones adicionales si no se conoce el `record_id`.

        Args:
            chat_id (int): ID del chat.
            conditions (dict): Diccionario con las condiciones adicionales:
                - category
                - amount
                - date
                - description
        """
        try:
            # Paso 1: Consultar ítems por `chat_id`
            response = self.table.query(
                KeyConditionExpression="chat_id = :chat_id",
                ExpressionAttributeValues={":chat_id": chat_id},
            )

            # Paso 2: Filtrar ítems localmente
            items = response.get("Items", [])
            item_to_delete = next(
                (
                    item
                    for item in items
                    if item.get("category") == conditions.get("category")
                    and item.get("amount") == conditions.get("amount")
                    and item.get("date") == conditions.get("date")
                    and item.get("description") == conditions.get("description")
                ),
                None,
            )

            if item_to_delete:
                # Paso 3: Eliminar el ítem identificado
                self.table.delete_item(
                    Key={
                        "chat_id": item_to_delete["chat_id"],
                        "record_id": item_to_delete["record_id"],
                    }
                )
                logger.info(f"Item eliminado con éxito: {item_to_delete}")
            else:
                logger.warning("No se encontró un ítem que cumpla con las condiciones.")
        except ClientError as e:
            logger.error(
                f"Error al eliminar el ítem con condiciones de {self.name}: {e}"
            )

    def get_value(self, chat_id: int, column: str) -> dict:
        """
        Recupera un valor de una columna específica para un `chat_id` dado.
        """
        try:
            response = self.table.get_item(Key={"chat_id": chat_id})
            item = response.get("Item", {})
            # Retorna el valor específico o None si no existe
            return item.get(column, None)
        except ClientError as e:
            logger.error(f"Error fetching item from {self.name}: {e}")
            return None


table = DynamoTable("TelegramBotUserExpenses")

table.delete_item_by_conditions(
    chat_id=123,
    conditions={
        "category": "a",
        "amount": 123,
        "date": "11-01-2025",
        "description": "123",
    },
)

chat_id = 123
user_name = "seba"
category = "a"
date = "11-01-2025"
amount = 123
description = "123"
Item = {
    "chat_id": chat_id,
    "user_name": user_name,
    "record_id": 124,
    "category": category,
    "date": date,
    "description": description,
    "amount": amount,
}

table.put_item(Item)
