from typing import Optional, List, Dict, Any
import urllib3
import json
import logging
from dataclasses import dataclass
from utils.utils import setup_logger

# Configuración del logger a nivel de módulo
logger = setup_logger(__name__)


@dataclass
class TelegramConfig:
    """Clase para configuración de Telegram."""

    token: str
    base_url: str = "https://api.telegram.org/bot"


class TelegramAPI:
    """Cliente para la API de Telegram."""

    def __init__(self, token: str) -> None:
        """
        Inicializa el cliente de Telegram.

        Args:
            token: Token de autenticación del bot
        """
        self._config = TelegramConfig(token=token)
        self._url = f"{self._config.base_url}{token}/"
        self._http = urllib3.PoolManager()

    def send_reply(
        self,
        chat_id: int,
        message: str,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        menu: Optional[List[List[str]]] = None,
    ) -> None:
        """
        Envía un mensaje de respuesta a un chat.

        Args:
            chat_id: ID del chat
            message: Mensaje a enviar
            buttons: Botones inline opcionales
            menu: Menú de teclado opcional
        """
        reply = self._build_reply_payload(chat_id, message, buttons, menu)
        self._make_request("sendMessage", reply)

    def delete_message(self, chat_id: int, message_id: int) -> None:
        """
        Elimina un mensaje específico de un chat.

        Args:
            chat_id: ID del chat
            message_id: ID del mensaje a eliminar
        """
        payload = {"chat_id": chat_id, "message_id": message_id}
        self._make_request("deleteMessage", payload)

    def _build_reply_payload(
        self,
        chat_id: int,
        message: str,
        buttons: Optional[List[List[Dict[str, str]]]] = None,
        menu: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Construye el payload para una respuesta.

        Args:
            chat_id: ID del chat
            message: Mensaje a enviar
            buttons: Botones inline opcionales
            menu: Menú de teclado opcional

        Returns:
            Dict con el payload formateado
        """
        payload = {"chat_id": chat_id, "text": message}

        if buttons:
            payload["reply_markup"] = {"inline_keyboard": buttons}
        elif menu:
            payload["reply_markup"] = {
                "keyboard": menu,
                "resize_keyboard": True,
                "one_time_keyboard": False,
            }

        return payload

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> None:
        """
        Realiza una petición HTTP a la API de Telegram.

        Args:
            endpoint: Endpoint de la API
            payload: Datos a enviar
        """
        encoded_data = json.dumps(payload).encode("utf-8")

        try:
            response = self._http.request(
                "POST",
                f"{self._url}{endpoint}",
                body=encoded_data,
                headers={"Content-Type": "application/json"},
            )
            logger.info(f"Request to {endpoint}: {encoded_data}")

            if response.status != 200:
                logger.error(f"Error en la petición: {response.status}")

        except Exception as e:
            logger.error(f"Error al realizar la petición: {str(e)}")
