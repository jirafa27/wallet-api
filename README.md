# Wallet API

## Описание

Этот проект представляет собой REST API для управления балансом кошельков.  
Поддерживаются операции пополнения (`DEPOSIT`), снятия (`WITHDRAW`) и получения информации о кошельке.

API разработано с использованием **Flask** и **PostgreSQL**.  
Система запускается в **Docker** с помощью `docker-compose`.

## Технологии

- **Backend**: Flask + SQLAlchemy
- **Database**: PostgreSQL
- **Migrations**: Flask-Migrate
- **Containerization**: Docker, Docker Compose
- **Testing**: Pytest

---

## Установка и запуск

```bash
git clone https://github.com/jirafa27/wallet-api.git
cd wallet-api
```

Для работы программы требуется создать в корне проекта .env файл
Пример .env файла

```bash
POSTGRES_DB=wallets_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
TEST_BASE_URL="http://app:5000/api/v1/wallets"
```

### Сборка и запуск контейнеров

Собрать контейнеры:

```sh
docker-compose build
```

Запустить сервисы в фоновом режиме:

```shell
docker-compose up -d
```

После запуска приложение будет доступно по адресу: ```http://127.0.0.1:5000```

Проверить работу API:
```curl -X GET http://127.0.0.1:5000/```

Для запуска тестов

````shell
docker-compose run --rm app pytest -vv
````

## API Эндпоинты

### 1. Создать кошелек

```POST /api/v1/wallets```

```sh
{
  "status": "success",
  "message": "Wallet created successfully",
  "wallet": {
    "UID": "d0a1e9d6-45b8-4c69-a17a-9384765e748a",
    "amount": 0.0
  }
}
```

### 2. Получить информацию о кошельке

``` GET /api/v1/wallets/{wallet_uid}```

```sh 
{
  "status": "success",
  "wallet": {
    "UID": "d0a1e9d6ww",
    "amount": 1000.0
  }
}
```

### 3. Провести операцию (пополнение или снятие)

```POST /api/v1/wallets/{wallet_uid}/operation```

Тело запроса:

```sh
{
  "operation_type": "DEPOSIT",
  "amount": 500
}
```

Пример ответа:

```sh
{
  "UID": "doa1eldlsd",
  "amount": 1500.0,
  "operation": "DEPOSIT",
  "status": "success"
}
```

### 4. Получить список всех кошельков

```GET /api/v1/wallets```

Пример ответа:

```sh
{
  "status": "success",
  "wallets": [
    {
      "UID": "doa1eldlsd",
      "amount": 1000.0
    },
    {
      "UID": "sfdagfgdfb",
      "amount": 500.0
    }
  ]
}
```

### 5. Удалить кошелек

```DELETE /api/v1/wallets```
Пример запроса:

```sh
{
  "wallet_uid": "d0a1e9d6qq"
}
```

Пример ответа:

```sh
{
  "status": "success",
  "message": "Wallet deleted successfully"
}
```
