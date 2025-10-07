"""FastAPI application for managing a barber shop."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .database import get_connection, init_db

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Barber Shop Manager", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=5)
    email: Optional[str]


class Customer(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]


class AppointmentCreate(BaseModel):
    customer_id: int
    service: str
    scheduled_for: datetime
    notes: Optional[str]


class Appointment(AppointmentCreate):
    id: int


class ProductCreate(BaseModel):
    name: str
    description: Optional[str]
    price: float
    stock: int = 0


class Product(ProductCreate):
    id: int


class ChatCreate(BaseModel):
    appointment_id: Optional[int]
    customer_name: str


class Chat(BaseModel):
    id: int
    appointment_id: Optional[int]
    customer_name: str
    created_at: datetime


class ChatMessageCreate(BaseModel):
    sender: str
    message: str


class ChatMessage(ChatMessageCreate):
    id: int
    chat_id: int
    created_at: datetime


@app.on_event("startup")
async def startup_event() -> None:
    init_db()


@app.post("/customers", response_model=Customer, status_code=201)
async def create_customer(customer: CustomerCreate) -> Customer:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO customers (name, phone, email) VALUES (?, ?, ?)",
            (customer.name, customer.phone, customer.email),
        )
        customer_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, name, phone, email FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
    return Customer(**dict(row))


@app.get("/customers", response_model=List[Customer])
async def list_customers() -> List[Customer]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, name, phone, email FROM customers").fetchall()
    return [Customer(**dict(row)) for row in rows]


@app.post("/appointments", response_model=Appointment, status_code=201)
async def create_appointment(appointment: AppointmentCreate) -> Appointment:
    with get_connection() as conn:
        customer_exists = conn.execute(
            "SELECT 1 FROM customers WHERE id = ?",
            (appointment.customer_id,),
        ).fetchone()
        if not customer_exists:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        cursor = conn.execute(
            """
            INSERT INTO appointments (customer_id, service, scheduled_for, notes)
            VALUES (?, ?, ?, ?)
            """,
            (
                appointment.customer_id,
                appointment.service,
                appointment.scheduled_for.isoformat(),
                appointment.notes,
            ),
        )
        appointment_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, customer_id, service, scheduled_for, notes FROM appointments WHERE id = ?",
            (appointment_id,),
        ).fetchone()

    return Appointment(
        id=row["id"],
        customer_id=row["customer_id"],
        service=row["service"],
        scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
        notes=row["notes"],
    )


@app.get("/appointments", response_model=List[Appointment])
async def list_appointments() -> List[Appointment]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, customer_id, service, scheduled_for, notes FROM appointments"
        ).fetchall()

    return [
        Appointment(
            id=row["id"],
            customer_id=row["customer_id"],
            service=row["service"],
            scheduled_for=datetime.fromisoformat(row["scheduled_for"]),
            notes=row["notes"],
        )
        for row in rows
    ]


@app.post("/appointments/{appointment_id}/photo", status_code=201)
async def upload_haircut_reference(
    appointment_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = None,
) -> dict:
    if file.content_type not in {"image/jpeg", "image/png"}:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado")

    with get_connection() as conn:
        appointment_exists = conn.execute(
            "SELECT 1 FROM appointments WHERE id = ?",
            (appointment_id,),
        ).fetchone()
        if not appointment_exists:
            raise HTTPException(status_code=404, detail="Cita no encontrada")

    file_path = UPLOAD_DIR / f"appointment_{appointment_id}_{file.filename}"
    with file_path.open("wb") as buffer:
        buffer.write(await file.read())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO haircut_references (appointment_id, file_path, description)
            VALUES (?, ?, ?)
            """,
            (appointment_id, str(file_path), description),
        )

    return {"status": "ok", "file_path": file_path.name}


@app.get("/appointments/{appointment_id}/photo/{photo_id}")
async def get_haircut_reference(appointment_id: int, photo_id: int) -> FileResponse:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT file_path FROM haircut_references
            WHERE id = ? AND appointment_id = ?
            """,
            (photo_id, appointment_id),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Referencia no encontrada")

    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no disponible")
    return FileResponse(path=file_path)


@app.post("/products", response_model=Product, status_code=201)
async def create_product(product: ProductCreate) -> Product:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO products (name, description, price, stock) VALUES (?, ?, ?, ?)",
            (product.name, product.description, product.price, product.stock),
        )
        product_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, name, description, price, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
    return Product(**dict(row))


@app.get("/products", response_model=List[Product])
async def list_products() -> List[Product]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, description, price, stock FROM products"
        ).fetchall()
    return [Product(**dict(row)) for row in rows]


@app.post("/chats", response_model=Chat, status_code=201)
async def create_chat(chat: ChatCreate) -> Chat:
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO chats (appointment_id, customer_name, created_at) VALUES (?, ?, ?)",
            (chat.appointment_id, chat.customer_name, created_at),
        )
        chat_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, appointment_id, customer_name, created_at FROM chats WHERE id = ?",
            (chat_id,),
        ).fetchone()

    return Chat(
        id=row["id"],
        appointment_id=row["appointment_id"],
        customer_name=row["customer_name"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@app.post("/chats/{chat_id}/messages", response_model=ChatMessage, status_code=201)
async def add_chat_message(chat_id: int, message: ChatMessageCreate) -> ChatMessage:
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        chat_exists = conn.execute(
            "SELECT 1 FROM chats WHERE id = ?",
            (chat_id,),
        ).fetchone()
        if not chat_exists:
            raise HTTPException(status_code=404, detail="Chat no encontrado")

        cursor = conn.execute(
            """
            INSERT INTO chat_messages (chat_id, sender, message, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, message.sender, message.message, created_at),
        )
        message_id = cursor.lastrowid
        row = conn.execute(
            """
            SELECT id, chat_id, sender, message, created_at
            FROM chat_messages WHERE id = ?
            """,
            (message_id,),
        ).fetchone()

    return ChatMessage(
        id=row["id"],
        chat_id=row["chat_id"],
        sender=row["sender"],
        message=row["message"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@app.get("/chats/{chat_id}/messages", response_model=List[ChatMessage])
async def list_chat_messages(chat_id: int) -> List[ChatMessage]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, chat_id, sender, message, created_at
            FROM chat_messages WHERE chat_id = ? ORDER BY created_at
            """,
            (chat_id,),
        ).fetchall()

    return [
        ChatMessage(
            id=row["id"],
            chat_id=row["chat_id"],
            sender=row["sender"],
            message=row["message"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
