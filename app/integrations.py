"""Optional production integrations for NORTHMEN (credentials are environment-only)."""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def http_json(url: str, *, method: str = "GET", payload=None, headers=None, timeout=15):
    body = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=body, method=method, headers={"Accept": "application/json", **(headers or {})})
    try:
        with urlopen(req, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw.decode()) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise RuntimeError(f"Serviço externo respondeu {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Não foi possível conectar ao serviço externo.") from exc


def mercado_pago_preference(order: dict, items: list[dict], payer: dict, public_url: str):
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Pagamento online indisponível: configure MERCADOPAGO_ACCESS_TOKEN.")
    payload = {
        "items": [{"title": i["product_name"], "quantity": i["quantity"], "currency_id": "BRL", "unit_price": float(i["unit_price"])} for i in items],
        "payer": {"name": payer["name"], "email": payer["email"]},
        "external_reference": str(order["id"]),
        "back_urls": {"success": public_url.rstrip("/") + "/payment-result.html?status=success", "pending": public_url.rstrip("/") + "/payment-result.html?status=pending", "failure": public_url.rstrip("/") + "/payment-result.html?status=failure"},
        "auto_return": "approved",
        "notification_url": public_url.rstrip("/") + "/api/store/payments/mercadopago/webhook",
        "statement_descriptor": "NORTHMEN",
    }
    result = http_json("https://api.mercadopago.com/checkout/preferences", method="POST", payload=payload,
                       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    if not result.get("init_point") or not result.get("id"):
        raise RuntimeError("O Mercado Pago não retornou um link de pagamento válido.")
    return result


def mercado_pago_payment(payment_id: str):
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Mercado Pago não configurado.")
    return http_json(f"https://api.mercadopago.com/v1/payments/{payment_id}",
                     headers={"Authorization": f"Bearer {token}"})


def melhor_envio_quote(destination_cep: str, products: list[dict]):
    token = os.getenv("MELHORENVIO_TOKEN", "").strip()
    origin = os.getenv("STORE_ORIGIN_CEP", "").strip()
    if not token or not origin:
        raise RuntimeError("Cotação indisponível: configure MELHORENVIO_TOKEN e STORE_ORIGIN_CEP.")
    package = {
        "from": {"postal_code": origin}, "to": {"postal_code": destination_cep},
        "products": [{"id": str(p["id"]), "width": float(os.getenv("STORE_PACKAGE_WIDTH_CM", "20")),
                      "height": float(os.getenv("STORE_PACKAGE_HEIGHT_CM", "8")),
                      "length": float(os.getenv("STORE_PACKAGE_LENGTH_CM", "30")),
                      "weight": float(os.getenv("STORE_PRODUCT_WEIGHT_KG", "0.4")),
                      "insurance_value": float(p["price"]), "quantity": int(p["quantity"])} for p in products],
        "options": {"receipt": False, "own_hand": False},
    }
    base = "https://sandbox.melhorenvio.com.br" if os.getenv("MELHORENVIO_ENV", "sandbox").lower() != "production" else "https://www.melhorenvio.com.br"
    result = http_json(base + "/api/v2/me/shipment/calculate", method="POST", payload=package,
                       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                "User-Agent": os.getenv("STORE_USER_AGENT", "NORTHMEN Store (suporte@northmen.com.br)")})
    quotes = []
    for q in result if isinstance(result, list) else []:
        price = q.get("custom_price") or q.get("price")
        if q.get("id") and price is not None and not q.get("error"):
            quotes.append({"id": str(q["id"]), "name": q.get("name") or q.get("company", {}).get("name", "Entrega"),
                           "price": round(float(price), 2), "delivery_days": q.get("custom_delivery_time") or q.get("delivery_time")})
    return quotes
