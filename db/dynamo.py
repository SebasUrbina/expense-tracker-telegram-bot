import boto3
from botocore.exceptions import ClientError


class DynamoTable:
    dynamodb = boto3.resource('dynamodb')

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
            print(f"Error saving item in {self.name}: {e}")

    def get_value(self, chat_id: int, column: str) -> dict:
        """
        Recupera un valor de una columna específica para un `chat_id` dado.
        """
        try:
            response = self.table.get_item(
                Key={'chat_id': chat_id}
            )
            item = response.get('Item', {})
            # Retorna el valor específico o None si no existe
            return item.get(column, None)
        except ClientError as e:
            print(f"Error fetching item from {self.name}: {e}")
            return None
