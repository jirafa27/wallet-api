import concurrent.futures
import os

import pytest
import requests

from app import app, db

BASE_URL = os.getenv("TEST_BASE_URL", "http://app:5000/api/v1/wallets")


@pytest.fixture(scope="function")
def client():
    """Создаёт тестовый клиент Flask и использует транзакцию для отката изменений после теста."""
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            connection = db.engine.connect()
            transaction = connection.begin()
            db.session.bind = connection

        yield client

        with app.app_context():
            transaction.rollback()
            connection.close()
            db.session.remove()


def test_create_wallet(client):
    """Тест создания кошелька."""
    response = client.post("/api/v1/wallets")
    assert response.status_code == 200

    data = response.get_json()
    assert "wallet" in data
    assert "UID" in data["wallet"]
    assert data["wallet"]["amount"] == 0.0


def test_get_wallet(client):
    """Тест получения информации о кошельке."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.get_json()["wallet"]["UID"] == wallet_id


def test_deposit(client):
    """Тест пополнения баланса кошелька."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    deposit_data = {"operation_type": "DEPOSIT", "amount": 1000}
    response = client.post(f"/api/v1/wallets/{wallet_id}/operation", json=deposit_data)

    assert response.status_code == 200
    assert response.get_json()["amount"] == 1000


def test_withdraw(client):
    """Тест снятия денег с кошелька."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 500},
    )
    assert response.status_code == 200
    assert response.get_json()["amount"] == 500


def test_withdraw_insufficient_funds(client):
    """Тест ошибки при недостатке средств."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 1000},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Insufficient funds"


def test_invalid_operation(client):
    """Тест ошибки при передаче неверного типа операции."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "INVALID", "amount": 1000},
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "Invalid operation_type"


def test_delete_wallet(client):
    """Тест удаления кошелька."""
    create_response = client.post("/api/v1/wallets")
    wallet_id = create_response.get_json()["wallet"]["UID"]

    response = client.delete("/api/v1/wallets", json={"wallet_uid": wallet_id})
    assert response.status_code == 200
    assert response.get_json()["message"] == "Wallet deleted successfully"

    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 404


def test_concurrent_transactions():
    """Тест конкурентных транзакций: пополнение и списание одновременно."""

    create_response = requests.post(f"{BASE_URL}")
    assert (
        create_response.status_code == 200
    ), f"Ошибка создания кошелька: {create_response.text}"
    wallet_id = create_response.json()["wallet"]["UID"]

    # Выполняем первоначальное пополнение для установки баланса 1000
    deposit_initial = requests.post(
        f"{BASE_URL}/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000},
    )
    assert (
        deposit_initial.status_code == 200
    ), f"Ошибка начального депозита: {deposit_initial.text}"

    # Определяем функции для параллельного выполнения
    def deposit():
        response = requests.post(
            f"{BASE_URL}/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 500},
        )
        return response.json()

    def withdraw():
        response = requests.post(
            f"{BASE_URL}/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 500},
        )
        return response.json()

    # Выполняем конкурентные операции одновременно
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Запускаем одновременно депозит и списание
        results = list(executor.map(lambda f: f(), [deposit, withdraw]))

    # Проверяем, что обе операции завершились успешно
    for result in results:
        assert result.get("status") == "success", f"Ошибка в операции: {result}"

    # Проверяем итоговый баланс кошелька
    response = requests.get(f"{BASE_URL}/{wallet_id}")
    assert response.status_code == 200, f"Ошибка получения баланса: {response.text}"
    final_balance = response.json()["wallet"]["amount"]

    assert final_balance == 1000, f"Баланс не сошелся: {final_balance} (ожидалось 1000)"


def test_get_all_wallets(client):
    """Тест получения всех доступных кошельков."""

    # Создаём несколько кошельков
    wallet1 = client.post("/api/v1/wallets").get_json()["wallet"]["UID"]
    wallet2 = client.post("/api/v1/wallets").get_json()["wallet"]["UID"]
    wallet3 = client.post("/api/v1/wallets").get_json()["wallet"]["UID"]

    # Делаем GET-запрос для получения всех кошельков
    response = client.get("/api/v1/wallets")

    assert response.status_code == 200, f"Ошибка получения кошельков: {response.text}"

    data = response.get_json()
    assert "wallets" in data, "Ответ не содержит ключ 'wallets'"
    assert isinstance(data["wallets"], list), "Ответ должен содержать список кошельков"

    # Проверяем, что созданные кошельки есть в списке
    wallet_ids = {wallet["UID"] for wallet in data["wallets"]}
    assert wallet1 in wallet_ids, "Первый кошелек отсутствует в списке"
    assert wallet2 in wallet_ids, "Второй кошелек отсутствует в списке"
    assert wallet3 in wallet_ids, "Третий кошелек отсутствует в списке"
