# app/schemas.py
import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth ---
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    org_id: uuid.UUID
    role: str


# --- Clients ---
class ClientIn(BaseModel):
    name: str
    email: EmailStr | None = None
    billing_address: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    billing_address: str | None = None


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr | None = None
    billing_address: str | None = None


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
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    client_name: str
    issue_date: date
    due_date: date
    total_cents: int
    balance_cents: int
    status: str
    currency: str


class InvoiceSummary(BaseModel):
    total_due_cents: int
    overdue_count: int
    paid_last_30d_cents: int
    upcoming_due_cents: int
    revenue_by_month: list[dict]  # [{ month: "YYYY-MM", total_cents: int, count: int }]


# --- Dashboard ---
class RevenueMonth(BaseModel):
    month: str  # "YYYY-MM"
    total_cents: int
    count: int


class DashboardSummaryOut(BaseModel):
    total_billed_cents: int
    total_due_cents: int
    overdue_count: int
    pending_count: int
    bkt_0_30: int | None = None
    bkt_31_60: int | None = None
    bkt_61_90: int | None = None
    bkt_90p: int | None = None
    revenue_by_month: list[RevenueMonth]
