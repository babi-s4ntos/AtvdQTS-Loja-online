import pytest
from fastapi.testclient import TestClient
from app import main
from tests.factories.product_factory import ProductFactory

pytestmark = pytest.mark.integration


def test_health_and_dashboard(client):
    assert client.get("/api/health").json()["status"] == "ok"
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert "revenue_month" in response.json()


def test_create_and_update_product(client):
    payload = {"name": "Jaqueta College", "category": "Jaquetas", "description": "Modelo urbano",
               "price": 299.9, "cost": 130, "image": "campaign-look.jpg"}
    created = client.post("/api/products", json=payload)
    assert created.status_code == 201
    product_id = created.json()["id"]
    updated = {**payload, "price": 319.9}
    assert client.put(f"/api/products/{product_id}", json=updated).json()["price"] == 319.9


def test_stock_movement_and_prevent_negative(client):
    product = client.get("/api/products").json()[0]
    movement = {"product_id": product["id"], "size": "XG", "color": "Azul",
                "movement_type": "entrada", "quantity": 4, "note": "Reposição"}
    assert client.post("/api/stock/movements", json=movement).status_code == 201
    movement.update({"movement_type": "saida", "quantity": 7})
    response = client.post("/api/stock/movements", json=movement)
    assert response.status_code == 400


def test_customer_and_sale_decrease_stock(client, fake):
    customer = client.post("/api/customers", json={
        "name": fake.name(), "email": fake.email(), "phone": fake.phone_number()
    }).json()
    product = client.get("/api/products").json()[0]
    stock = client.get("/api/stock").json()
    variant = next(x for x in stock if x["product_id"] == product["id"] and x["size"] == "M" and x["color"] == "Preto")
    before = variant["quantity"]
    sale = client.post("/api/sales", json={
        "customer_id": customer["id"], "discount": 5, "payment_method": "Pix",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    })
    assert sale.status_code == 201
    assert sale.json()["total"] == round(product["price"] - 5, 2)
    after = client.get("/api/stock").json()
    variant_after = next(x for x in after if x["id"] == variant["id"])
    assert variant_after["quantity"] == before - 1


def test_sale_rejects_insufficient_stock(client):
    product = client.get("/api/products").json()[0]
    response = client.post("/api/sales", json={
        "customer_name": "Teste", "discount": 0, "payment_method": "Dinheiro",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 999}]
    })
    assert response.status_code == 400


def test_sale_uses_mocked_notification_service(client, mocker):
    product = client.get("/api/products").json()[0]
    mocked_notify = mocker.patch("app.main.notify_sale_created")
    response = client.post("/api/sales", json={
        "customer_name": "Cliente teste", "discount": 0, "payment_method": "Pix",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    })
    assert response.status_code == 201
    mocked_notify.assert_called_once_with(response.json()["id"], response.json()["total"])


def test_product_factory_creates_valid_synthetic_data(client):
    payload = ProductFactory.build()
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == payload["name"]



def test_notification_failure_does_not_break_sale(client, mocker):
    product = client.get("/api/products").json()[0]

    mocked_notify = mocker.patch(
        "app.main.notify_sale_created",
        side_effect=RuntimeError("serviço indisponível"),
    )

    response = client.post(
        "/api/sales",
        json={
            "customer_name": "Cliente teste",
            "discount": 0,
            "payment_method": "Pix",
            "items": [
                {
                    "product_id": product["id"],
                    "size": "M",
                    "color": "Preto",
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 201
    mocked_notify.assert_called_once_with(
        response.json()["id"],
        response.json()["total"],
    )



def test_reports(client):
    response = client.get("/api/reports")
    assert response.status_code == 200
    assert "products" in response.json()
    assert "low_stock" in response.json()


def register_customer(client, fake):
    return client.post("/api/store/register", json={
        "name": fake.name(), "email": fake.unique.email(), "phone": fake.phone_number(), "password": "SenhaForte123"
    })


def test_store_public_pages_and_product_variants(client):
    assert client.get("/").status_code == 200
    assert client.get("/admin", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/store/products").status_code == 200
    product = client.get("/api/store/products").json()[0]
    detail = client.get(f"/api/store/products/{product['id']}")
    assert detail.status_code == 200
    assert detail.json()["variants"]
    assert "cost" not in product


def test_customer_registration_login_and_protected_history(client, fake):
    created = register_customer(client, fake)
    assert created.status_code == 201
    token = created.json()["token"]
    assert client.get("/api/store/orders").status_code == 401
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/store/me", headers=headers).json()["email"] == created.json()["customer"]["email"]
    login = client.post("/api/store/login", json={"email": created.json()["customer"]["email"], "password": "SenhaForte123"})
    assert login.status_code == 200
    assert client.post("/api/store/login", json={"email": created.json()["customer"]["email"], "password": "wrongpass"}).status_code == 401


def test_store_order_pending_approval_updates_stock_and_admin_sales(client, fake):
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    detail = client.get(f"/api/store/products/{product['id']}").json()
    variant = next(v for v in detail["variants"] if v["size"] == "M" and v["color"] == "Preto")
    before = variant["quantity"]
    order = client.post("/api/store/orders", headers=headers, json={
        "payment_method": "Pagamento na entrega", "cep": "11900000", "address": "Rua Teste, 123, Centro", "shipping_service": "test-service", "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    })
    assert order.status_code == 201
    assert order.json()["status"] == "Pendente"
    assert client.get("/api/store/orders", headers=headers).json()[0]["id"] == order.json()["id"]
    assert client.get("/api/store/admin/orders").status_code == 200
    approved = client.post(f"/api/store/admin/orders/{order.json()['id']}/approve")
    assert approved.status_code == 200
    assert client.get("/api/stock").json()
    after_detail = client.get(f"/api/store/products/{product['id']}").json()
    after = next(v["quantity"] for v in after_detail["variants"] if v["size"] == "M" and v["color"] == "Preto")
    assert after == before - 1
    assert any(s["customer_name"] == registration["customer"]["name"] for s in client.get("/api/sales").json())
    assert client.post(f"/api/store/admin/orders/{order.json()['id']}/approve").status_code == 409


def test_store_order_rejects_insufficient_stock(client, fake):
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    response = client.post("/api/store/orders", headers=headers, json={
        "payment_method": "Pagamento na entrega", "cep": "11900000", "address": "Rua Teste, 123, Centro", "shipping_service": "test-service", "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 20}]
    })
    assert response.status_code == 409


def test_admin_api_requires_basic_auth(client):
    assert client.get("/api/dashboard", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/customers", headers={"Authorization": ""}).status_code == 401
    assert client.get("/api/health").status_code == 200


def test_store_pages_and_assets_are_served(client):
    for page in ("products", "product", "cart", "checkout", "login", "register", "account"):
        response = client.get(f"/{page}.html")
        assert response.status_code == 200
        assert "<title>" in response.text or "<title " in response.text
    assert client.get("/static/store/assets/css/store.css").status_code == 200
    assert client.get("/static/store/assets/js/store.js").status_code == 200


def test_shipping_quote_returns_provider_options(client, fake):
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    response = client.post("/api/store/shipping/quote", headers=headers, json={
        "cep": "11900-000", "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    })
    assert response.status_code == 200
    assert response.json()[0]["id"] == "test-service"


def test_online_order_rejects_manual_approval(client, fake, monkeypatch):
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://northmen.example")
    monkeypatch.setattr("app.main.mercado_pago_preference", lambda order, items, payer, url: {"id": "pref-1", "init_point": "https://checkout.example/pay"})
    order = client.post("/api/store/orders", headers=headers, json={
        "payment_method": "Mercado Pago", "cep": "11900000", "address": "Rua Teste, 123, Centro", "shipping_service": "test-service",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    })
    assert order.status_code == 201
    assert order.json()["checkout_url"].startswith("https://")
    assert client.post(f"/api/store/admin/orders/{order.json()['id']}/approve").status_code == 409


def test_customer_pages_and_payment_return_are_served(client):
    assert client.get("/payment-result.html").status_code == 200
    assert client.get("/api/health").json()["status"] == "ok"


def test_mercadopago_webhook_validates_signature_and_confirms_payment(client, fake, monkeypatch):
    import hashlib
    import hmac
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "test-token")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://northmen.example")
    monkeypatch.setenv("MERCADOPAGO_WEBHOOK_SECRET", "webhook-secret")
    monkeypatch.setattr("app.main.mercado_pago_preference", lambda *args: {"id": "pref-webhook", "init_point": "https://checkout.example/pay"})
    order = client.post("/api/store/orders", headers=headers, json={
        "payment_method": "Mercado Pago", "cep": "11900000", "address": "Rua Teste, 123, Centro", "shipping_service": "test-service",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    }).json()
    payment_id, request_id, ts = "payment-123", "request-123", "1700000000"
    manifest = f"id:{payment_id};request-id:{request_id};ts:{ts};"
    signature = hmac.new(b"webhook-secret", manifest.encode(), hashlib.sha256).hexdigest()
    monkeypatch.setattr("app.main.mercado_pago_payment", lambda pid: {
        "id": pid, "status": "approved", "external_reference": str(order["id"]), "transaction_amount": order["total"]
    })
    response = client.post(f"/api/store/payments/mercadopago/webhook?data.id={payment_id}", headers={
        "x-signature": f"ts={ts},v1={signature}", "x-request-id": request_id
    })
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/api/store/orders", headers=headers).json()[0]["status"] == "Aprovado"
    assert client.post(f"/api/store/payments/mercadopago/webhook?data.id={payment_id}", headers={
        "x-signature": f"ts={ts},v1={signature}", "x-request-id": request_id
    }).status_code == 200


def test_admin_can_register_tracking_code_for_approved_order(client, fake):
    registration = register_customer(client, fake).json()
    headers = {"Authorization": f"Bearer {registration['token']}"}
    product = client.get("/api/store/products").json()[0]
    order = client.post("/api/store/orders", headers=headers, json={
        "payment_method": "Pagamento na entrega", "cep": "11900000", "address": "Rua Teste, 123, Centro", "shipping_service": "test-service",
        "items": [{"product_id": product["id"], "size": "M", "color": "Preto", "quantity": 1}]
    }).json()
    assert client.post(f"/api/store/admin/orders/{order['id']}/approve").status_code == 200
    response = client.put(f"/api/store/admin/orders/{order['id']}/tracking", json={"tracking_code": "AB123456789BR"})
    assert response.status_code == 200
    assert client.get("/api/store/orders", headers=headers).json()[0]["tracking_code"] == "AB123456789BR"


def test_production_startup_fails_closed_without_secrets(monkeypatch):
    import pytest
    monkeypatch.setenv("APP_ENV", "production")
    for key in ("ADMIN_USERNAME", "ADMIN_PASSWORD", "STORE_SECRET", "MERCADOPAGO_ACCESS_TOKEN",
                "MERCADOPAGO_WEBHOOK_SECRET", "MELHORENVIO_TOKEN", "STORE_ORIGIN_CEP", "PUBLIC_BASE_URL"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="Configuração de produção incompleta"):
        with TestClient(main.app):
            pass
