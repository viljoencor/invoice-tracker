# app/schemas.py
import uuid
from datetime import date

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


# --- Clients ---
class ClientIn(BaseModel):
    name: str
    email: EmailStr | None = None
    billing_address: str | None = None


class ClientOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr | None = None
    billing_address: str | None = None

    class Config:
        from_attributes = True


# --- Invoices ---
class InvoiceItemIn(BaseModel):
    description: str
    qty: float = Field(gt=0)
    unit_price_cents: int = Field(ge=0)
    tax_rate_bp: int = 0


class InvoiceCreate(BaseModel):
    client_id: uuid.UUID
    issue_date: date
    due_date: date
    currency: str = "ZAR"
    notes: str | None = None
    items: list[InvoiceItemIn]


class InvoiceOut(BaseModel):
    id: uuid.UUID
    number: str
    client_id: uuid.UUID
    issue_date: date
    due_date: date
    currency: str
    subtotal_cents: int
    tax_cents: int
    total_cents: int
    balance_cents: int
    status: str

    class Config:
        from_attributes = True


# Detail view includes client_name
class InvoiceDetail(InvoiceOut):
    client_name: str


class PaymentIn(BaseModel):
    invoice_id: uuid.UUID
    amount_cents: int = Field(gt=0)
    received_at: date
    method: str | None = None
    reference: str | None = None


class InvoiceList(BaseModel):
    id: uuid.UUID
    number: str
    client_name: str
    issue_date: date
    due_date: date
    total_cents: int
    balance_cents: int
    status: str
    currency: str

    class Config:
        from_attributes = True


class InvoiceSummary(BaseModel):
    total_due_cents: int
    overdue_count: int
    paid_last_30d_cents: int
    upcoming_due_cents: int
    revenue_by_month: list[dict]  # [{ month: "YYYY-MM", total_cents: int, count: int }]
