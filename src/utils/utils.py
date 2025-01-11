import logging
import re
from typing import Optional


def extract_cell_range_from_message(message: str) -> Optional[str]:
    """
    Extrae el rango de celdas de un mensaje que contiene una referencia a celdas de Excel/Google Sheets.

    Args:
        message (str): El mensaje que contiene el rango de celdas.

    Returns:
        Optional[str]: El rango de celdas (ej: 'A1:B10') si se encuentra, None si no se encuentra.
    """
    # Busca el texto que está después de "📊 Celda: " hasta el final de la línea
    match = re.search(r"([A-Z0-9]+:+[A-Z0-9]+)", message)
    if match:
        return match.group(1)
    return None


def is_google_sheet_url(message: str) -> bool:
    """
    Verifica si una URL corresponde a una hoja de Google Sheets.

    Args:
        message (str): La URL a verificar.

    Returns:
        bool: True si es una URL válida de Google Sheets, False en caso contrario.
    """
    return (
        re.match(r"https://docs.google.com/spreadsheets/d/[A-Z0-9]+", message)
        is not None
    )


def extract_data_from_message(message: str) -> dict:
    """
    Extrae información estructurada de un mensaje que contiene datos de una transacción.

    Args:
        message (str): El mensaje que contiene los datos de la transacción.

    Returns:
        dict: Diccionario con los campos extraídos:
            - categoria (str): Categoría de la transacción
            - fecha (str): Fecha de la transacción
            - descripcion (str): Descripción de la transacción
            - monto (str): Monto de la transacción (sin el símbolo $)
    """
    regex = {
        "category": r"Categoría: (.+)",
        "date": r"Fecha: (.+)",
        "description": r"Descripción: (.+)",
        "amount": r"Monto: \$([\d]+)",
    }

    # Extraer los datos usando las expresiones regulares
    datos = {
        campo: re.search(patron, message).group(1) for campo, patron in regex.items()
    }
    return datos


def extract_sheet_id_from_message(message: str) -> Optional[str]:
    """
    Extrae el ID de una hoja de Google Sheets desde una URL.

    Args:
        message (str): La URL de Google Sheets que contiene el ID.

    Returns:
        Optional[str]: El ID de la hoja de Google Sheets si se encuentra, None si no se encuentra.
    """
    # Busca el ID de la hoja de Google Sheets en la URL
    match = re.search(
        r"https://docs\.google\.com/spreadsheets/d/([A-Za-z0-9_-]+)", message
    )
    if match:
        return match.group(1)
    return None


def setup_logger(name):
    """
    Configura un logger con un formato que incluye el nombre del archivo,
    el nivel del log, la línea y el mensaje.

    Args:
        name (str): Nombre del logger (generalmente el nombre del módulo o script).

    Returns:
        logging.Logger: Logger configurado.
    """
    # Crear el logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Nivel de logs

    # Formato de los logs
    formatter = logging.Formatter(
        "%(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # Handler para consola (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Agregar el handler al logger
    if not logger.hasHandlers():  # Evitar duplicados si ya está configurado
        logger.addHandler(console_handler)

    return logger
