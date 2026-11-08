
from __future__ import annotations

import os
import sqlite3
import base64
import hashlib
import hmac
import json
import secrets
import time
import logging

from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

from app.integrations import (
    mercado_pago_preference,
    mercado_pago_payment,
    melhor_envio_quote,
)


# ---------------------------------------------------------
# CONFIGURAÇÕES
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "northmen.db"))

STORE_SECRET = os.getenv(
    "STORE_SECRET",
    "change-this-store-secret-before-production"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# BANCO DE DADOS
# ---------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def notify_sale_created(sale_id: int, total: float):
    """Ponto de integração para notificações externas."""
    return {
        "queued": True,
        "sale_id": sale_id,
        "total": total,
    }


def init_db():
    with get_conn() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL CHECK(price >= 0),
            cost REAL NOT NULL DEFAULT 0 CHECK(cost >= 0),
            image TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            size TEXT NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            UNIQUE(product_id, size, color)
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER REFERENCES customers(id),
            customer_name TEXT NOT NULL,
            total REAL NOT NULL,
            discount REAL NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            product_name TEXT NOT NULL,
            size TEXT NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            unit_cost REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            subtotal REAL NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Aguardando confirmação',
            status TEXT NOT NULL DEFAULT 'Pendente',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id),
            product_name TEXT NOT NULL,
            size TEXT NOT NULL,
            color TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            size TEXT NOT NULL,
            color TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
        """)

        # Atualização de colunas para bancos já existentes.
        order_columns = {
            row[1]
            for row in db.execute("PRAGMA table_info(orders)").fetchall()
        }

        new_order_columns = {
            "shipping_cost": "REAL NOT NULL DEFAULT 0",
            "shipping_service": "TEXT DEFAULT ''",
            "shipping_cep": "TEXT DEFAULT ''",
            "shipping_address": "TEXT DEFAULT ''",
            "payment_provider_id": "TEXT DEFAULT ''",
            "payment_external_reference": "TEXT DEFAULT ''",
            "tracking_code": "TEXT DEFAULT ''",
        }

        for column, declaration in new_order_columns.items():
            if column not in order_columns:
                db.execute(
                    f"ALTER TABLE orders ADD COLUMN {column} {declaration}"
                )

        customer_columns = {
            row[1]
            for row in db.execute("PRAGMA table_info(customers)").fetchall()
        }

        if "password_hash" not in customer_columns:
            db.execute("""
                ALTER TABLE customers
                ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''
            """)

        db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email
            ON customers(email COLLATE NOCASE)
            WHERE email <> ''
        """)

        # Dados demonstrativos para ambiente de desenvolvimento.
        count = db.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0]

        if (
            count == 0
            and os.getenv("SEED_DEMO_DATA", "true").lower() == "true"
            and os.getenv("APP_ENV", "development") != "production"
        ):
            seed = [
                (
                    "Camiseta Essential",
                    "Camisetas",
                    "Algodão premium, modelagem regular.",
                    89.90,
                    34.00,
                    "campaign-look.jpg",
                ),
                (
                    "Camiseta Oversized",
                    "Camisetas",
                    "Caimento amplo e toque macio.",
                    119.90,
                    48.00,
                    "campaign-skate.jpg",
                ),
                (
                    "Moletom Urban",
                    "Moletons",
                    "Moletom encorpado para dias frios.",
                    229.90,
                    105.00,
                    "campaign-closeup.jpg",
                ),
                (
                    "Bermuda Cargo",
                    "Calças e bermudas",
                    "Bolsos utilitários e visual urbano.",
                    149.90,
                    62.00,
                    "campaign-look.jpg",
                ),
            ]

            for item in seed:
                cur = db.execute(
                    """
                    INSERT INTO products(
                        name, category, description, price, cost, image
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    item,
                )

                product_id = cur.lastrowid

                for size, color, quantity in [
                    ("P", "Preto", 8),
                    ("M", "Preto", 12),
                    ("G", "Preto", 7),
                    ("M", "Off-white", 6),
                    ("G", "Off-white", 4),
                ]:
                    db.execute(
                        """
                        INSERT INTO stock(
                            product_id, size, color, quantity
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (product_id, size, color, quantity),
                    )

            db.execute(
                """
                INSERT INTO customers(name, email, phone, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Cliente demonstração",
                    "cliente@exemplo.com",
                    "(13) 99999-0000",
                    datetime.now().isoformat(),
                ),
            )


# ---------------------------------------------------------
# MODELOS PYDANTIC
# ---------------------------------------------------------

class ProductIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=60)
    description: str = ""
    price: float = Field(gt=0)
    cost: float = Field(ge=0)
    image: str = ""


class ProductOut(ProductIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_total: int = 0
    active: bool = True


class StockIn(BaseModel):
    product_id: int
    size: str = Field(min_length=1, max_length=10)
    color: str = Field(min_length=1, max_length=40)
    movement_type: Literal["entrada", "saida"]
    quantity: int = Field(gt=0)
    note: str = ""


class CustomerIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = ""
    phone: str = ""


class SaleItemIn(BaseModel):
    product_id: int
    size: str
    color: str
    quantity: int = Field(gt=0)


class SaleIn(BaseModel):
    customer_id: int | None = None
    customer_name: str = "Cliente balcão"
    discount: float = Field(default=0, ge=0)

    payment_method: Literal[
        "Pix",
        "Cartão de crédito",
        "Cartão de débito",
        "Dinheiro",
    ]

    items: list[SaleItemIn] = Field(min_length=1)


# ---------------------------------------------------------
# INICIALIZAÇÃO FASTAPI
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("APP_ENV", "development") == "production":
        required = [
            "ADMIN_USERNAME",
            "ADMIN_PASSWORD",
            "STORE_SECRET",
            "MERCADOPAGO_ACCESS_TOKEN",
            "MERCADOPAGO_WEBHOOK_SECRET",
            "MELHORENVIO_TOKEN",
            "STORE_ORIGIN_CEP",
            "PUBLIC_BASE_URL",
        ]

        missing = [
            key
            for key in required
            if not os.getenv(key, "").strip()
        ]

        if missing:
            raise RuntimeError(
                "Configuração de produção incompleta: "
                + ", ".join(missing)
            )

        if (
            os.getenv("ADMIN_PASSWORD") == "northmen-admin-change-me"
            or len(os.getenv("STORE_SECRET", "")) < 32
        ):
            raise RuntimeError(
                "Defina senha administrativa própria e STORE_SECRET "
                "com pelo menos 32 caracteres."
            )

        if not os.getenv("PUBLIC_BASE_URL", "").startswith("https://"):
            raise RuntimeError(
                "PUBLIC_BASE_URL precisa usar HTTPS em produção."
            )

    init_db()
    yield


app = FastAPI(
    title="NORTHMEN | Gestão",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "app" / "static"),
    name="static",
)


# ---------------------------------------------------------
# AUTENTICAÇÃO ADMINISTRATIVA
# ---------------------------------------------------------

@app.middleware("http")
async def admin_access_control(request: Request, call_next):
    path = request.url.path

    admin_page = path == "/admin"

    admin_api = (
        path.startswith("/api/")
        and path != "/api/health"
        and not (
            path.startswith("/api/store/")
            and not path.startswith("/api/store/admin/")
        )
    )

    if admin_page or admin_api:
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv(
            "ADMIN_PASSWORD",
            "northmen-admin-change-me",
        )

        if (
            os.getenv("APP_ENV", "development") == "production"
            and (
                username == "admin"
                or password == "northmen-admin-change-me"
            )
        ):
            return JSONResponse(
                {
                    "detail": (
                        "Credenciais administrativas de produção "
                        "não configuradas."
                    )
                },
                status_code=503,
            )

        auth = request.headers.get("authorization", "")

        try:
            scheme, encoded = auth.split(" ", 1)

            decoded = base64.b64decode(
                encoded,
                validate=True,
            ).decode()

            supplied_user, supplied_pass = decoded.split(":", 1)

        except Exception:
            scheme = ""
            supplied_user = ""
            supplied_pass = ""

        if (
            scheme.lower() != "basic"
            or not hmac.compare_digest(supplied_user, username)
            or not hmac.compare_digest(supplied_pass, password)
        ):
            return JSONResponse(
                {"detail": "Autenticação administrativa necessária."},
                status_code=401,
                headers={
                    "WWW-Authenticate": 'Basic realm="NORTHMEN Admin"'
                },
            )

    return await call_next(request)


# ---------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------

@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "app" / "static" / "store" / "index.html"
    )


@app.get("/admin")
def admin_home():
    return FileResponse(
        BASE_DIR / "app" / "static" / "index.html"
    )


@app.get("/{store_page}.html")
def store_page(store_page: str):
    allowed = {
        "products",
        "product",
        "cart",
        "checkout",
        "login",
        "register",
        "account",
        "payment-result",
    }

    if store_page not in allowed:
        raise HTTPException(404, "Página não encontrada.")

    return FileResponse(
        BASE_DIR / "app" / "static" / "store" / f"{store_page}.html"
    )


# ---------------------------------------------------------
# SAÚDE DA APLICAÇÃO
# ---------------------------------------------------------

@app.get("/api/health")
def health():
    payment_ready = bool(
        os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        and os.getenv("MERCADOPAGO_WEBHOOK_SECRET")
        and os.getenv("PUBLIC_BASE_URL", "").startswith("https://")
    )

    shipping_ready = bool(
        os.getenv("MELHORENVIO_TOKEN")
        and os.getenv("STORE_ORIGIN_CEP")
    )

    return {
        "status": "ok",
        "database": "sqlite",
        "payment_configured": payment_ready,
        "shipping_configured": shipping_ready,
        "ready_for_online_sales": payment_ready and shipping_ready,
    }


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.get("/api/dashboard")
def dashboard():
    with get_conn() as db:
        today = date.today().isoformat()
        month = datetime.now().strftime("%Y-%m")

        revenue = db.execute(
            """
            SELECT COALESCE(SUM(total), 0)
            FROM sales
            WHERE substr(created_at, 1, 7) = ?
            """,
            (month,),
        ).fetchone()[0]

        sales_count = db.execute(
            """
            SELECT COUNT(*)
            FROM sales
            WHERE substr(created_at, 1, 10) = ?
            """,
            (today,),
        ).fetchone()[0]

        profit = db.execute(
            """
            SELECT COALESCE(
                SUM(
                    (si.unit_price * si.quantity)
                    - (si.unit_cost * si.quantity)
                ),
                0
            )
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            WHERE substr(s.created_at, 1, 7) = ?
            """,
            (month,),
        ).fetchone()[0]

        low_stock = db.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT product_id
                FROM stock
                GROUP BY product_id
                HAVING SUM(quantity) <= 5
            )
            """
        ).fetchone()[0]

        total_products = db.execute(
            "SELECT COUNT(*) FROM products WHERE active = 1"
        ).fetchone()[0]

        latest = db.execute(
            """
            SELECT id, customer_name, total, payment_method, created_at
            FROM sales
            ORDER BY id DESC
            LIMIT 5
            """
        ).fetchall()

        return {
            "revenue_month": round(revenue, 2),
            "sales_today": sales_count,
            "estimated_profit": round(profit, 2),
            "low_stock_products": low_stock,
            "active_products": total_products,
            "recent_sales": [dict(x) for x in latest],
        }


# ---------------------------------------------------------
# PRODUTOS - ADMINISTRAÇÃO
# ---------------------------------------------------------

@app.get("/api/products")
def list_products(q: str = "", category: str = ""):
    with get_conn() as db:
        rows = db.execute(
            """
            SELECT p.*, COALESCE(SUM(s.quantity), 0) stock_total
            FROM products p
            LEFT JOIN stock s ON s.product_id = p.id
            WHERE p.active = 1
            AND p.name LIKE ?
            AND p.category LIKE ?
            GROUP BY p.id
            ORDER BY p.id DESC
            """,
            (f"%{q}%", f"%{category}%"),
        ).fetchall()

        return [dict(r) for r in rows]


@app.post("/api/products", status_code=201)
def create_product(data: ProductIn):
    with get_conn() as db:
        cur = db.execute(
            """
            INSERT INTO products(
                name, category, description, price, cost, image
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.category,
                data.description,
                data.price,
                data.cost,
                data.image,
            ),
        )

        return {
            "id": cur.lastrowid,
            **data.model_dump(),
            "stock_total": 0,
        }


@app.put("/api/products/{product_id}")
def update_product(product_id: int, data: ProductIn):
    with get_conn() as db:
        cur = db.execute(
            """
            UPDATE products
            SET name = ?, category = ?, description = ?,
                price = ?, cost = ?, image = ?
            WHERE id = ? AND active = 1
            """,
            (
                data.name,
                data.category,
                data.description,
                data.price,
                data.cost,
                data.image,
                product_id,
            ),
        )

        if cur.rowcount == 0:
            raise HTTPException(404, "Produto não encontrado.")

        return {
            "id": product_id,
            **data.model_dump(),
        }


@app.delete("/api/products/{product_id}")
def delete_product(product_id: int):
    with get_conn() as db:
        cur = db.execute(
            """
            UPDATE products
            SET active = 0
            WHERE id = ? AND active = 1
            """,
            (product_id,),
        )

        if cur.rowcount == 0:
            raise HTTPException(404, "Produto não encontrado.")

        return {
            "message": "Produto arquivado com sucesso."
        }


# ---------------------------------------------------------
# ESTOQUE
# ---------------------------------------------------------

@app.get("/api/stock")
def list_stock():
    with get_conn() as db:
        rows = db.execute(
            """
            SELECT
                s.id,
                s.product_id,
                p.name product_name,
                s.size,
                s.color,
                s.quantity
            FROM stock s
            JOIN products p ON p.id = s.product_id
            WHERE p.active = 1
            ORDER BY p.name, s.size, s.color
            """
        ).fetchall()

        return [dict(r) for r in rows]


@app.post("/api/stock/movements", status_code=201)
def stock_movement(data: StockIn):
    with get_conn() as db:
        product = db.execute(
            "SELECT id FROM products WHERE id = ? AND active = 1",
            (data.product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(404, "Produto não encontrado.")

        row = db.execute(
            """
            SELECT id, quantity
            FROM stock
            WHERE product_id = ? AND size = ? AND color = ?
            """,
            (data.product_id, data.size, data.color),
        ).fetchone()

        current = row["quantity"] if row else 0

        if data.movement_type == "entrada":
            new_qty = current + data.quantity
        else:
            new_qty = current - data.quantity

        if new_qty < 0:
            raise HTTPException(
                400,
                "Estoque insuficiente para essa saída.",
            )

        if row:
            db.execute(
                "UPDATE stock SET quantity = ? WHERE id = ?",
                (new_qty, row["id"]),
            )
        else:
            db.execute(
                """
                INSERT INTO stock(product_id, size, color, quantity)
                VALUES (?, ?, ?, ?)
                """,
                (
                    data.product_id,
                    data.size,
                    data.color,
                    new_qty,
                ),
            )

        db.execute(
            """
            INSERT INTO stock_movements(
                product_id, size, color, movement_type,
                quantity, note, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.product_id,
                data.size,
                data.color,
                data.movement_type,
                data.quantity,
                data.note,
                datetime.now().isoformat(),
            ),
        )

        return {
            "message": "Movimentação registrada.",
            "new_quantity": new_qty,
        }


# ---------------------------------------------------------
# CLIENTES
# ---------------------------------------------------------

@app.get("/api/customers")
def list_customers(q: str = ""):
    with get_conn() as db:
        rows = db.execute(
            """
            SELECT
                c.id,
                c.name,
                c.email,
                c.phone,
                c.created_at,
                COUNT(s.id) purchases,
                COALESCE(SUM(s.total), 0) total_spent
            FROM customers c
            LEFT JOIN sales s ON s.customer_id = c.id
            WHERE c.name LIKE ?
            GROUP BY c.id
            ORDER BY c.id DESC
            """,
            (f"%{q}%",),
        ).fetchall()

        return [dict(r) for r in rows]


@app.post("/api/customers", status_code=201)
def create_customer(data: CustomerIn):
    with get_conn() as db:
        cur = db.execute(
            """
            INSERT INTO customers(name, email, phone, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.name,
                data.email,
                data.phone,
                datetime.now().isoformat(),
            ),
        )

        return {
            "id": cur.lastrowid,
            **data.model_dump(),
            "purchases": 0,
            "total_spent": 0,
        }


# ---------------------------------------------------------
# VENDAS
# ---------------------------------------------------------

@app.get("/api/sales")
def list_sales():
    with get_conn() as db:
        rows = db.execute(
            "SELECT * FROM sales ORDER BY id DESC LIMIT 100"
        ).fetchall()

        return [dict(r) for r in rows]


@app.post("/api/sales", status_code=201)
def create_sale(data: SaleIn):
    with get_conn() as db:
        customer = None

        if data.customer_id:
            customer = db.execute(
                "SELECT * FROM customers WHERE id = ?",
                (data.customer_id,),
            ).fetchone()

            if not customer:
                raise HTTPException(404, "Cliente não encontrado.")

        customer_name = (
            customer["name"]
            if customer
            else data.customer_name
        )

        resolved = []
        subtotal = 0.0

        for item in data.items:
            product = db.execute(
                """
                SELECT *
                FROM products
                WHERE id = ? AND active = 1
                """,
                (item.product_id,),
            ).fetchone()

            if not product:
                raise HTTPException(
                    404,
                    f"Produto {item.product_id} não encontrado.",
                )

            stock = db.execute(
                """
                SELECT *
                FROM stock
                WHERE product_id = ? AND size = ? AND color = ?
                """,
                (item.product_id, item.size, item.color),
            ).fetchone()

            if not stock or stock["quantity"] < item.quantity:
                raise HTTPException(
                    400,
                    f"Estoque insuficiente: {product['name']} "
                    f"({item.size}/{item.color}).",
                )

            subtotal += product["price"] * item.quantity
            resolved.append((item, product, stock))

        if data.discount > subtotal:
            raise HTTPException(
                400,
                "O desconto não pode ser maior que o subtotal.",
            )

        total = round(subtotal - data.discount, 2)

        cur = db.execute(
            """
            INSERT INTO sales(
                customer_id,
                customer_name,
                total,
                discount,
                payment_method,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data.customer_id,
                customer_name,
                total,
                data.discount,
                data.payment_method,
                datetime.now().isoformat(),
            ),
        )

        sale_id = cur.lastrowid

        for item, product, stock in resolved:
            db.execute(
                """
                UPDATE stock
                SET quantity = quantity - ?
                WHERE id = ?
                """,
                (item.quantity, stock["id"]),
            )

            db.execute(
                """
                INSERT INTO sale_items(
                    sale_id,
                    product_id,
                    product_name,
                    size,
                    color,
                    quantity,
                    unit_price,
                    unit_cost
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    product["id"],
                    product["name"],
                    item.size,
                    item.color,
                    item.quantity,
                    product["price"],
                    product["cost"],
                ),
            )

        # A falha da notificação não pode cancelar uma venda.
        try:
            notify_sale_created(sale_id, total)
        except Exception:
            logger.exception(
                "Não foi possível enviar a notificação da venda %s",
                sale_id,
            )

        return {
            "id": sale_id,
            "customer_name": customer_name,
            "subtotal": round(subtotal, 2),
            "discount": data.discount,
            "total": total,
            "payment_method": data.payment_method,
        }


# ---------------------------------------------------------
# RELATÓRIOS
# ---------------------------------------------------------

@app.get("/api/reports")
def reports():
    with get_conn() as db:
        products = db.execute(
            """
            SELECT
                p.id,
                p.name,
                p.category,
                COALESCE(SUM(si.quantity), 0) units_sold,
                COALESCE(
                    SUM(si.quantity * (si.unit_price - si.unit_cost)),
                    0
                ) gross_profit
            FROM products p
            LEFT JOIN sale_items si ON si.product_id = p.id
            WHERE p.active = 1
            GROUP BY p.id
            ORDER BY units_sold DESC
            """
        ).fetchall()

        low = db.execute(
            """
            SELECT
                p.name,
                s.size,
                s.color,
                s.quantity
            FROM stock s
            JOIN products p ON p.id = s.product_id
            WHERE s.quantity <= 3 AND p.active = 1
            ORDER BY s.quantity ASC
            """
        ).fetchall()

        return {
            "products": [dict(r) for r in products],
            "low_stock": [dict(r) for r in low],
        }


# =========================================================
# LOJA VIRTUAL
# =========================================================

# ---------------------------------------------------------
# MODELOS DA LOJA
# ---------------------------------------------------------

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=160)
    phone: str = Field(default="", max_length=30)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str
    password: str


class OrderItemIn(BaseModel):
    product_id: int
    size: str = Field(min_length=1, max_length=10)
    color: str = Field(min_length=1, max_length=40)
    quantity: int = Field(gt=0, le=20)


class ShippingQuoteIn(BaseModel):
    cep: str = Field(pattern=r"^\d{5}-?\d{3}$")
    items: list[OrderItemIn] = Field(min_length=1, max_length=30)


class OrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=30)

    payment_method: Literal[
        "Mercado Pago",
        "Pagamento na entrega",
    ]

    cep: str = Field(pattern=r"^\d{5}-?\d{3}$")
    address: str = Field(min_length=5, max_length=240)
    shipping_service: str = Field(min_length=1, max_length=30)


class TrackingIn(BaseModel):
    tracking_code: str = Field(min_length=5, max_length=40)


# ---------------------------------------------------------
# SENHAS E TOKENS
# ---------------------------------------------------------

def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt,
        240_000,
    )

    return base64.urlsafe_b64encode(
        salt + digest
    ).decode()


def _verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(stored.encode())

        salt = raw[:16]
        expected = raw[16:]

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            240_000,
        )

        return hmac.compare_digest(actual, expected)

    except Exception:
        return False


def _issue_token(customer_id: int) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({
            "sub": customer_id,
            "exp": int(time.time()) + 60 * 60 * 24 * 7,
        }).encode()
    ).decode().rstrip("=")

    signature = hmac.new(
        STORE_SECRET.encode(),
        payload.encode(),
        hashlib.sha256,
    ).digest()

    return (
        payload
        + "."
        + base64.urlsafe_b64encode(signature).decode().rstrip("=")
    )


def _current_customer(request: Request):
    auth = request.headers.get("authorization", "")

    token = (
        auth[7:]
        if auth.lower().startswith("bearer ")
        else request.cookies.get("northmen_session", "")
    )

    try:
        payload, signature = token.split(".", 1)

        expected = hmac.new(
            STORE_SECRET.encode(),
            payload.encode(),
            hashlib.sha256,
        ).digest()

        supplied = base64.urlsafe_b64decode(
            signature + "=" * (-len(signature) % 4)
        )

        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Assinatura inválida.")

        data = json.loads(
            base64.urlsafe_b64decode(
                payload + "=" * (-len(payload) % 4)
            )
        )

        if data["exp"] < time.time():
            raise ValueError("Token expirado.")

        with get_conn() as db:
            row = db.execute(
                """
                SELECT id, name, email, phone
                FROM customers
                WHERE id = ?
                """,
                (data["sub"],),
            ).fetchone()

            if not row:
                raise ValueError("Cliente não encontrado.")

            return dict(row)

    except Exception:
        raise HTTPException(
            401,
            "Faça login para continuar.",
        )


# ---------------------------------------------------------
# PRODUTOS DA LOJA
# ---------------------------------------------------------

@app.get("/api/store/products")
def store_products(q: str = "", category: str = ""):
    with get_conn() as db:
        rows = db.execute(
            """
            SELECT
                p.id,
                p.name,
                p.category,
                p.description,
                p.price,
                p.image,
                COALESCE(SUM(s.quantity), 0) stock_total
            FROM products p
            LEFT JOIN stock s ON s.product_id = p.id
            WHERE p.active = 1
            AND p.name LIKE ?
            AND p.category LIKE ?
            GROUP BY p.id
            ORDER BY p.id DESC
            """,
            (f"%{q}%", f"%{category}%"),
        ).fetchall()

        return [dict(r) for r in rows]


@app.get("/api/store/products/{product_id}")
def store_product(product_id: int):
    with get_conn() as db:
        product = db.execute(
            """
            SELECT id, name, category, description, price, image
            FROM products
            WHERE id = ? AND active = 1
            """,
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(
                404,
                "Produto não encontrado.",
            )

        variants = db.execute(
            """
            SELECT size, color, quantity
            FROM stock
            WHERE product_id = ? AND quantity > 0
            ORDER BY size, color
            """,
            (product_id,),
        ).fetchall()

        return {
            **dict(product),
            "variants": [dict(v) for v in variants],
        }


# ---------------------------------------------------------
# CADASTRO E LOGIN DA LOJA
# ---------------------------------------------------------

@app.post("/api/store/register", status_code=201)
def store_register(data: RegisterIn):
    email = data.email.strip().lower()

    with get_conn() as db:
        existing = db.execute(
            """
            SELECT 1
            FROM customers
            WHERE email = ? COLLATE NOCASE
            """,
            (email,),
        ).fetchone()

        if existing:
            raise HTTPException(
                409,
                "Este e-mail já está cadastrado.",
            )

        cur = db.execute(
            """
            INSERT INTO customers(
                name, email, phone, password_hash, created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.name.strip(),
                email,
                data.phone.strip(),
                _hash_password(data.password),
                datetime.now().isoformat(),
            ),
        )

        customer_id = cur.lastrowid

    return {
        "token": _issue_token(customer_id),
        "customer": {
            "id": customer_id,
            "name": data.name.strip(),
            "email": email,
            "phone": data.phone.strip(),
        },
    }


@app.post("/api/store/login")
def store_login(data: LoginIn):
    with get_conn() as db:
        row = db.execute(
            """
            SELECT id, name, email, phone, password_hash
            FROM customers
            WHERE email = ? COLLATE NOCASE
            """,
            (data.email.strip(),),
        ).fetchone()

        if (
            not row
            or not row["password_hash"]
            or not _verify_password(
                data.password,
                row["password_hash"],
            )
        ):
            raise HTTPException(
                401,
                "E-mail ou senha incorretos.",
            )

        customer = {
            key: row[key]
            for key in ("id", "name", "email", "phone")
        }

    return {
        "token": _issue_token(customer["id"]),
        "customer": customer,
    }


@app.get("/api/store/me")
def store_me(customer: dict = Depends(_current_customer)):
    return customer


# ---------------------------------------------------------
# HISTÓRICO DE PEDIDOS
# ---------------------------------------------------------

@app.get("/api/store/orders")
def store_order_history(
    customer: dict = Depends(_current_customer),
):
    with get_conn() as db:
        orders = db.execute(
            """
            SELECT
                id,
                subtotal,
                total,
                payment_method,
                payment_status,
                status,
                created_at,
                shipping_cost,
                shipping_service,
                shipping_cep,
                tracking_code
            FROM orders
            WHERE customer_id = ?
            ORDER BY id DESC
            """,
            (customer["id"],),
        ).fetchall()

        result = []

        for order in orders:
            items = db.execute(
                """
                SELECT
                    product_name,
                    size,
                    color,
                    quantity,
                    unit_price
                FROM order_items
                WHERE order_id = ?
                """,
                (order["id"],),
            ).fetchall()

            result.append({
                **dict(order),
                "items": [dict(x) for x in items],
            })

        return result


# ---------------------------------------------------------
# COTAÇÃO DE FRETE
# ---------------------------------------------------------

@app.post("/api/store/shipping/quote")
def store_shipping_quote(
    data: ShippingQuoteIn,
    customer: dict = Depends(_current_customer),
):
    with get_conn() as db:
        resolved = []

        for item in data.items:
            product = db.execute(
                """
                SELECT id, name, price
                FROM products
                WHERE id = ? AND active = 1
                """,
                (item.product_id,),
            ).fetchone()

            stock = db.execute(
                """
                SELECT quantity
                FROM stock
                WHERE product_id = ? AND size = ? AND color = ?
                """,
                (
                    item.product_id,
                    item.size,
                    item.color,
                ),
            ).fetchone()

            if (
                not product
                or not stock
                or stock["quantity"] < item.quantity
            ):
                raise HTTPException(
                    409,
                    "Produto ou estoque indisponível para cotação.",
                )

            resolved.append({
                "id": product["id"],
                "price": product["price"],
                "quantity": item.quantity,
            })

    try:
        quotes = melhor_envio_quote(
            data.cep.replace("-", ""),
            resolved,
        )

    except RuntimeError as exc:
        raise HTTPException(503, str(exc))

    if not quotes:
        raise HTTPException(
            502,
            "Nenhuma modalidade de entrega disponível para este CEP.",
        )

    return quotes


# ---------------------------------------------------------
# CRIAÇÃO DE PEDIDOS
# ---------------------------------------------------------

@app.post("/api/store/orders", status_code=201)
def store_create_order(
    data: OrderIn,
    request: Request,
    customer: dict = Depends(_current_customer),
):
    with get_conn() as db:
        resolved = []
        subtotal = 0.0

        for item in data.items:
            product = db.execute(
                """
                SELECT id, name, price
                FROM products
                WHERE id = ? AND active = 1
                """,
                (item.product_id,),
            ).fetchone()

            if not product:
                raise HTTPException(
                    404,
                    "Um dos produtos não está mais disponível.",
                )

            stock = db.execute(
                """
                SELECT quantity
                FROM stock
                WHERE product_id = ? AND size = ? AND color = ?
                """,
                (
                    item.product_id,
                    item.size,
                    item.color,
                ),
            ).fetchone()

            if not stock or stock["quantity"] < item.quantity:
                raise HTTPException(
                    409,
                    f"Estoque insuficiente para {product['name']} "
                    f"({item.size}/{item.color}).",
                )

            subtotal += product["price"] * item.quantity
            resolved.append((item, product))

        # O frete é recalculado no servidor.
        try:
            quotes = melhor_envio_quote(
                data.cep.replace("-", ""),
                [
                    {
                        "id": product["id"],
                        "price": product["price"],
                        "quantity": item.quantity,
                    }
                    for item, product in resolved
                ],
            )

        except RuntimeError as exc:
            raise HTTPException(503, str(exc))

        quote = next(
            (
                q
                for q in quotes
                if q["id"] == data.shipping_service
            ),
            None,
        )

        if not quote:
            raise HTTPException(
                409,
                "A opção de frete expirou. Faça uma nova cotação.",
            )

        total = round(subtotal + quote["price"], 2)

        cur = db.execute(
            """
            INSERT INTO orders(
                customer_id,
                subtotal,
                total,
                payment_method,
                created_at,
                shipping_cost,
                shipping_service,
                shipping_cep,
                shipping_address
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer["id"],
                round(subtotal, 2),
                total,
                data.payment_method,
                datetime.now().isoformat(),
                quote["price"],
                quote["name"],
                data.cep.replace("-", ""),
                data.address.strip(),
            ),
        )

        order_id = cur.lastrowid

        for item, product in resolved:
            db.execute(
                """
                INSERT INTO order_items(
                    order_id,
                    product_id,
                    product_name,
                    size,
                    color,
                    quantity,
                    unit_price
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    product["id"],
                    product["name"],
                    item.size,
                    item.color,
                    item.quantity,
                    product["price"],
                ),
            )

        order = dict(
            db.execute(
                "SELECT * FROM orders WHERE id = ?",
                (order_id,),
            ).fetchone()
        )

        items = [
            dict(x)
            for x in db.execute(
                "SELECT * FROM order_items WHERE order_id = ?",
                (order_id,),
            ).fetchall()
        ]

    result = {
        "id": order_id,
        "status": "Pendente",
        "payment_status": "Aguardando pagamento",
        "subtotal": round(subtotal, 2),
        "shipping_cost": quote["price"],
        "shipping_service": quote["name"],
        "total": total,
        "payment_method": data.payment_method,
    }

    if data.payment_method == "Mercado Pago":
        public_url = os.getenv(
            "PUBLIC_BASE_URL",
            "",
        ).strip()

        if (
            not public_url.startswith("https://")
            and os.getenv("APP_ENV", "development") == "production"
        ):
            raise HTTPException(
                503,
                "Configure PUBLIC_BASE_URL com HTTPS para habilitar pagamentos online.",
            )

        if not public_url:
            raise HTTPException(
                503,
                "Configure PUBLIC_BASE_URL antes de habilitar o checkout de pagamento.",
            )

        try:
            preference = mercado_pago_preference(
                order,
                items,
                customer,
                public_url,
            )

        except RuntimeError as exc:
            with get_conn() as db:
                db.execute(
                    "DELETE FROM orders WHERE id = ?",
                    (order_id,),
                )

            raise HTTPException(503, str(exc))

        with get_conn() as db:
            db.execute(
                """
                UPDATE orders
                SET payment_provider_id = ?,
                    payment_external_reference = ?
                WHERE id = ?
                """,
                (
                    preference["id"],
                    str(order_id),
                    order_id,
                ),
            )

        result["checkout_url"] = preference["init_point"]

        result["message"] = (
            "Pedido criado. Conclua o pagamento no ambiente "
            "seguro do Mercado Pago."
        )

    else:
        result["message"] = (
            "Pedido criado. O pagamento será combinado na entrega; "
            "aguarde a confirmação da loja."
        )

    return result


# ---------------------------------------------------------
# APROVAÇÃO DE PEDIDOS PAGOS
# ---------------------------------------------------------

def _approve_paid_order(order_id: int, payment_id: str):
    with get_conn() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

        if not order:
            raise HTTPException(
                404,
                "Pedido não encontrado.",
            )

        if order["status"] == "Aprovado":
            return {
                "order_id": order_id,
                "status": "Aprovado",
                "duplicate": True,
            }

        if order["status"] != "Pendente":
            raise HTTPException(
                409,
                "Pedido não está pendente.",
            )

        items = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()

        customer = db.execute(
            "SELECT name FROM customers WHERE id = ?",
            (order["customer_id"],),
        ).fetchone()

        if not customer:
            raise HTTPException(
                404,
                "Cliente do pedido não encontrado.",
            )

        # Verifica todo o estoque antes de registrar a venda.
        for item in items:
            stock = db.execute(
                """
                SELECT id, quantity
                FROM stock
                WHERE product_id = ? AND size = ? AND color = ?
                """,
                (
                    item["product_id"],
                    item["size"],
                    item["color"],
                ),
            ).fetchone()

            if not stock or stock["quantity"] < item["quantity"]:
                raise HTTPException(
                    409,
                    "Estoque insuficiente para concluir o pedido pago; "
                    "contate o cliente.",
                )

        sale = db.execute(
            """
            INSERT INTO sales(
                customer_id,
                customer_name,
                total,
                discount,
                payment_method,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                order["customer_id"],
                customer["name"],
                order["total"],
                0,
                order["payment_method"],
                datetime.now().isoformat(),
            ),
        )

        sale_id = sale.lastrowid

        for item in items:
            product = db.execute(
                "SELECT cost FROM products WHERE id = ?",
                (item["product_id"],),
            ).fetchone()

            db.execute(
                """
                UPDATE stock
                SET quantity = quantity - ?
                WHERE product_id = ? AND size = ? AND color = ?
                """,
                (
                    item["quantity"],
                    item["product_id"],
                    item["size"],
                    item["color"],
                ),
            )

            db.execute(
                """
                INSERT INTO sale_items(
                    sale_id,
                    product_id,
                    product_name,
                    size,
                    color,
                    quantity,
                    unit_price,
                    unit_cost
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sale_id,
                    item["product_id"],
                    item["product_name"],
                    item["size"],
                    item["color"],
                    item["quantity"],
                    item["unit_price"],
                    product["cost"] if product else 0,
                ),
            )

        db.execute(
            """
            UPDATE orders
            SET status = 'Aprovado',
                payment_status = 'Pagamento aprovado',
                payment_provider_id = COALESCE(
                    NULLIF(?, ''),
                    payment_provider_id
                )
            WHERE id = ?
            """,
            (payment_id, order_id),
        )

        # A falha da notificação não desfaz a aprovação do pedido.
        try:
            notify_sale_created(sale_id, order["total"])
        except Exception:
            logger.exception(
                "Não foi possível enviar a notificação "
                "da venda %s, referente ao pedido %s",
                sale_id,
                order_id,
            )

        return {
            "order_id": order_id,
            "sale_id": sale_id,
            "status": "Aprovado",
            "total": order["total"],
        }


# ---------------------------------------------------------
# WEBHOOK MERCADO PAGO
# ---------------------------------------------------------

@app.post("/api/store/payments/mercadopago/webhook")
def mercadopago_webhook(request: Request):
    # Validação HMAC do webhook.
    secret = os.getenv(
        "MERCADOPAGO_WEBHOOK_SECRET",
        "",
    ).strip()

    signature = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")
    data_id = request.query_params.get("data.id", "")

    if not secret or not signature or not request_id or not data_id:
        raise HTTPException(
            401,
            "Webhook sem assinatura/configuração válida.",
        )

    try:
        parts = {
            part.split("=", 1)[0].strip(): part.split("=", 1)[1].strip()
            for part in signature.split(",")
            if "=" in part
        }

        timestamp = parts.get("ts", "")
        received = parts.get("v1", "")

        if not timestamp or not received:
            raise ValueError("Assinatura incompleta.")

        manifest = (
            f"id:{data_id};"
            f"request-id:{request_id};"
            f"ts:{timestamp};"
        )

        expected = hmac.new(
            secret.encode(),
            manifest.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, received):
            raise ValueError("Assinatura inválida.")

    except Exception:
        raise HTTPException(
            401,
            "Assinatura do webhook inválida.",
        )

    try:
        payment = mercado_pago_payment(data_id)

    except RuntimeError as exc:
        raise HTTPException(503, str(exc))

    if payment.get("status") != "approved":
        return {
            "received": True,
            "status": payment.get("status", "unknown"),
        }

    try:
        order_id = int(payment.get("external_reference", "0"))
    except (TypeError, ValueError):
        raise HTTPException(
            400,
            "Referência do pedido inválida.",
        )

    with get_conn() as db:
        order = db.execute(
            "SELECT total FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

    if not order:
        raise HTTPException(
            404,
            "Pedido não encontrado.",
        )

    try:
        paid_amount = float(
            payment.get("transaction_amount", 0)
        )
    except (TypeError, ValueError):
        raise HTTPException(
            400,
            "Valor do pagamento inválido.",
        )

    if abs(paid_amount - float(order["total"])) > 0.01:
        raise HTTPException(
            400,
            "Pagamento não corresponde ao pedido.",
        )

    _approve_paid_order(
        order_id,
        str(data_id),
    )

    return {
        "received": True,
        "order_id": order_id,
        "status": "approved",
    }


# ---------------------------------------------------------
# ADMINISTRAÇÃO DE PEDIDOS
# ---------------------------------------------------------

@app.get("/api/store/admin/orders")
def store_admin_orders():
    with get_conn() as db:
        rows = db.execute(
            """
            SELECT
                o.*,
                c.name customer_name,
                c.email,
                c.phone
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            ORDER BY o.id DESC
            """
        ).fetchall()

        result = []

        for row in rows:
            items = db.execute(
                """
                SELECT
                    product_name,
                    size,
                    color,
                    quantity,
                    unit_price
                FROM order_items
                WHERE order_id = ?
                """,
                (row["id"],),
            ).fetchall()

            result.append({
                **dict(row),
                "items": [dict(x) for x in items],
            })

        return result


@app.post("/api/store/admin/orders/{order_id}/approve")
def store_approve_order(order_id: int):
    with get_conn() as db:
        order = db.execute(
            "SELECT * FROM orders WHERE id = ?",
            (order_id,),
        ).fetchone()

        if not order:
            raise HTTPException(
                404,
                "Pedido não encontrado.",
            )

        if order["status"] != "Pendente":
            raise HTTPException(
                409,
                "Este pedido já foi processado.",
            )

        if (
            order["payment_method"] == "Mercado Pago"
            and order["payment_status"] != "Pagamento aprovado"
        ):
            raise HTTPException(
                409,
                "Não é possível aprovar manualmente um pedido "
                "de pagamento online sem confirmação do gateway.",
            )

    return _approve_paid_order(order_id, "")


@app.post("/api/store/admin/orders/{order_id}/cancel")
def store_cancel_order(order_id: int):
    with get_conn() as db:
        cur = db.execute(
            """
            UPDATE orders
            SET status = 'Cancelado'
            WHERE id = ? AND status = 'Pendente'
            """,
            (order_id,),
        )

        if not cur.rowcount:
            raise HTTPException(
                404,
                "Pedido pendente não encontrado.",
            )

        return {
            "id": order_id,
            "status": "Cancelado",
        }


@app.put("/api/store/admin/orders/{order_id}/tracking")
def store_update_tracking(
    order_id: int,
    data: TrackingIn,
):
    tracking_code = data.tracking_code.strip().upper()

    with get_conn() as db:
        cur = db.execute(
            """
            UPDATE orders
            SET tracking_code = ?
            WHERE id = ? AND status = 'Aprovado'
            """,
            (tracking_code, order_id),
        )

        if not cur.rowcount:
            raise HTTPException(
                404,
                "Pedido aprovado não encontrado.",
            )

    return {
        "order_id": order_id,
        "tracking_code": tracking_code,
    }


# ---------------------------------------------------------
# EXECUÇÃO DIRETA
# ---------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
