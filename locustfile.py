
"""
Cenário de carga para endpoints públicos da NORTHMEN Store.

Execução:
uv run locust -f locustfile.py --host http://127.0.0.1:8000

Interface:
http://localhost:8089
"""

from locust import HttpUser, between, task


class StoreVisitor(HttpUser):
    """Simula visitantes navegando pela loja virtual."""

    wait_time = between(1, 3)

    @task(3)
    def browse_products(self):
        with self.client.get(
            "/api/store/products",
            name="/api/store/products",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Falha ao carregar produtos: HTTP {response.status_code}"
                )

    @task(2)
    def open_home(self):
        with self.client.get(
            "/",
            name="/",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Falha ao carregar página inicial: HTTP {response.status_code}"
                )

    @task(1)
    def check_health(self):
        with self.client.get(
            "/api/health",
            name="/api/health",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Health check falhou: HTTP {response.status_code}"
                )
