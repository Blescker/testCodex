# Barber Shop Manager + Demo de modelo de anemia

Aplicación base construida con [FastAPI](https://fastapi.tiangolo.com/) para gestionar los servicios de una barbería y ahora incluir una **demo de predicción de anemia sin hemoglobina** usando un modelo `joblib`.

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

## Demo: modelo de anemia (`joblib`)

La API intenta cargar el modelo desde:

- `app/models/anemia_model.joblib` (por defecto), o
- variable de entorno `ANEMIA_MODEL_PATH`

Ejemplo:

```bash
export ANEMIA_MODEL_PATH=/ruta/a/tu/modelo.joblib
```

### Features esperadas

```python
FEATURES = [
    "RIDAGEYR", "RIAGENDR", "RIDEXPRG",
    "LBXIRN", "LBXUIB", "LBDTIB", "LBDPCT",
    "LBXFER", "LBXHSCRP",
    "LBXRBCSI", "LBXMCVSI", "LBXMCHSI",
    "LBXMC", "LBXRDW"
]
```

### Endpoints de la demo

- `GET /anemia/features`: devuelve la lista de columnas esperadas por el modelo.
- `POST /anemia/predict`: recibe un JSON con las 14 features y retorna:
  - `prediction` (valor numérico del modelo)
  - `prediction_label` (`anemia` o `sin_anemia` cuando la salida sea 0/1)
  - `probability` (si el modelo implementa `predict_proba`)

Ejemplo de request:

```bash
curl -X POST "http://127.0.0.1:8000/anemia/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "RIDAGEYR": 45,
    "RIAGENDR": 1,
    "RIDEXPRG": 0,
    "LBXIRN": 70,
    "LBXUIB": 240,
    "LBDTIB": 310,
    "LBDPCT": 22,
    "LBXFER": 40,
    "LBXHSCRP": 1.1,
    "LBXRBCSI": 4.7,
    "LBXMCVSI": 88,
    "LBXMCHSI": 29,
    "LBXMC": 33,
    "LBXRDW": 13.2
  }'
```

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
├── models/          # Ubicación sugerida para modelos .joblib
└── uploads/         # Almacenamiento local de referencias fotográficas
```

La base de datos SQLite (`barber_shop.db`) se genera automáticamente al iniciar la aplicación.
