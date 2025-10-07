# Barber Shop Manager

Aplicación base construida con [FastAPI](https://fastapi.tiangolo.com/) para gestionar los servicios de una barbería: citas, referencias fotográficas, chat con clientes y catálogo de productos.

## Requisitos

- Python 3.10+
- pip

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows usa `.venv\\Scripts\\activate`
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

El servidor se iniciará en `http://127.0.0.1:8000`. La documentación interactiva de la API está disponible en `http://127.0.0.1:8000/docs`.

## Funcionalidades principales

- **Clientes**: registrar y listar información de contacto.
- **Citas**: agendar servicios indicando fecha/hora, notas y cliente asociado.
- **Referencias fotográficas**: subir imágenes (PNG/JPG) por cita para almacenar el estilo deseado.
- **Chat**: abrir conversaciones vinculadas a una cita y registrar mensajes entre el cliente y el barbero para coordinar precios o detalles.
- **Productos**: administrar un catálogo de productos (ceras, polvos texturizadores, etc.) con precio y stock disponible.

## Estructura de carpetas

```
app/
├── database.py      # Manejo de SQLite y creación de tablas
├── main.py          # Definición de la API FastAPI
└── uploads/         # Almacenamiento local de referencias fotográficas
```

La base de datos SQLite (`barber_shop.db`) se genera automáticamente al iniciar la aplicación.
