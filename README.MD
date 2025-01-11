# Serverless Expense-Tracker Telegram Bot and Google Sheets

Bot serverless que permite registrar gastos automáticamente en Google Sheets a través de Telegram. Utiliza AWS Lambda y DynamoDB para el procesamiento y almacenamiento de datos.

## Características

- 📊 Integración con Google Sheets
- 💬 Interface a través de Telegram
- 🗄️ Almacenamiento en DynamoDB
- 📱 Categorización de gastos
- 🔄 Procesamiento serverless
- ⚡ Respuesta en tiempo real

## Arquitectura

El bot está construido con una arquitectura serverless utilizando:

- AWS Lambda para el procesamiento de mensajes
- DynamoDB para almacenar sesiones y gastos
- Google Sheets API para el registro de transacciones
- Telegram Bot API para la interfaz de usuario

## Funcionalidades

### Comandos Principales

- `/start` - Inicia el bot y solicita URL de Google Sheets. 
> Se debe compartir el Google Sheet con la cuenta de servicio proporcionada.
- Registro de gastos en formato: `DD-MM descripción monto` o `descripción monto`


## Configuración

### Configurar Lambda y DynamoDB

### Requisitos Previos

1. Cuenta de AWS con acceso a Lambda y DynamoDB
2. Bot de Telegram registrado (token)
3. Proyecto en Google Cloud con Sheets API habilitada
4. Google Sheet compartido con la cuenta de servicio

### Variables de Entorno

```bash
BOT_TOKEN=your_telegram_bot_token
GCP_MAIL_EDITOR=your_google_service_account
```

### Despliegue

1. Instalar dependencias:
```bash
pip install --target ./package --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib boto3
```

2. Crear archivo ZIP para Lambda:
```bash
cd package
zip -r ../deploy.zip .
cd ../src/
zip ../deploy.zip */* lambda_function.py ../credentials.json
```

## Uso

1. Inicia el bot con `/start`
2. Comparte tu Google Sheet con la cuenta de servicio proporcionada
3. Envía la URL del Google Sheet
4. Selecciona una categoría
5. Registra gastos en formato: `DD-MM descripción monto`

## Estructura de Datos

### DynamoDB

- Tabla `TelegramBotUserSession`: Almacena configuración de usuarios
- Tabla `TelegramBotUserExpenses`: Registra historial de gastos

### Google Sheets

El bot registra automáticamente:
- Fecha
- Descripción
- Categoría
- Monto

## Contribución

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios mayores.