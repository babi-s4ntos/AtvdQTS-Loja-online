import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from faker import Faker

from app import main


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"

    monkeypatch.setattr(main, "DB_PATH", db_file)

    main.init_db()

    monkeypatch.setattr(
        main,
        "melhor_envio_quote",
        lambda cep, products: [
            {
                "id": "test-service",
                "name": "Correios PAC (teste)",
                "price": 18.50,
                "delivery_days": 5,
            }
        ],
    )

    with TestClient(
        main.app,
        headers={
            "Authorization": "Basic YWRtaW46bm9ydGhtZW4tYWRtaW4tY2hhbmdlLW1l"
        },
    ) as test_client:
        yield test_client


@pytest.fixture()
def fake():
    return Faker("pt_BR")


@pytest.fixture(scope="session")
def live_server():
    """
    Inicia o servidor FastAPI uma única vez durante os testes
    E2E e de acessibilidade.
    """

    project_root = Path(__file__).resolve().parents[1]

    host = "127.0.0.1"
    port = 8000

    server_process = None

    def server_is_running():
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False

    # Inicia o servidor somente se a porta ainda estiver livre.
    if not server_is_running():
        env = os.environ.copy()

        server_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=str(project_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

    try:
        # Aguarda o servidor ficar disponível.
        deadline = time.time() + 30

        while time.time() < deadline:
            if server_is_running():
                break

            if (
                server_process is not None
                and server_process.poll() is not None
            ):
                raise RuntimeError(
                    "O servidor FastAPI encerrou antes de iniciar. "
                    "Verifique os erros de inicialização do Uvicorn."
                )

            time.sleep(0.5)

        else:
            raise RuntimeError(
                "O servidor FastAPI não iniciou em 30 segundos."
            )

        yield

    finally:
        # Encerra somente o processo iniciado por esta fixture.
        if server_process is not None:
            server_process.terminate()

            try:
                server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()