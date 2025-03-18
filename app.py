import os

from flask import Flask, jsonify, request
from flask_migrate import Migrate

from models import db, Wallet

app = Flask(__name__)

# Загружаем настройки из переменных окружения
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://user:password@postgres:5432/wallets_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)


@app.route("/")
def hello():
    return "Hello, Wallets!"


@app.route("/api/v1/wallets/<wallet_uid>/operation", methods=["POST"])
def wallet_operation(wallet_uid):
    db.session.begin()
    wallet = Wallet.query.filter_by(UID=wallet_uid).with_for_update().first()

    if not wallet:
        db.session.rollback()
        return jsonify({"error": "Wallet not found"}), 404

    data = request.json
    operation_type = data.get("operation_type")
    amount = data.get("amount")

    if operation_type not in ("DEPOSIT", "WITHDRAW"):
        db.session.rollback()
        return jsonify({"error": "Invalid operation_type"}), 400

    if not isinstance(amount, (int, float)) or amount <= 0:
        db.session.rollback()
        return jsonify({"error": "Amount must be positive number"}), 400

    try:
        if operation_type == "DEPOSIT":
            wallet.amount += amount
        elif operation_type == "WITHDRAW":
            if wallet.amount < amount:
                db.session.rollback()
                return jsonify({"error": "Insufficient funds"}), 400
            wallet.amount -= amount

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Transaction failed", "details": str(e)}), 500

    return (
        jsonify(
            {
                "UID": wallet.UID,
                "amount": wallet.amount,
                "operation": operation_type,
                "status": "success",
            }
        ),
        200,
    )


@app.route("/api/v1/wallets/<wallet_uid>", methods=["GET"])
def wallet_get(wallet_uid):
    wallet = Wallet.query.filter_by(UID=wallet_uid).first()
    if not wallet:
        return jsonify({"error": "Wallet not found"}), 404

    return (
        jsonify(
            {
                "status": "success",
                "wallet": {
                    "UID": wallet.UID,
                    "amount": wallet.amount,
                },
            }
        ),
        200,
    )


@app.post("/api/v1/wallets")
def create_wallet():
    """Дополнительный метод для создания кошелька"""
    wallet = Wallet()
    db.session.add(wallet)
    db.session.commit()
    db.session.refresh(wallet)
    return (
        jsonify(
            {
                "status": "success",
                "message": "Wallet created successfully",
                "wallet": wallet.to_dict(),
            }
        ),
        200,
    )


@app.delete("/api/v1/wallets")
def delete_wallet():
    """Дополнительный метод для удаления кошелька"""
    data = request.json
    wallet_uid = data.get("wallet_uid")

    wallet = Wallet.query.filter_by(UID=wallet_uid).first()
    if not wallet:
        return jsonify({"status": "error", "message": "Wallet not found"}), 404

    db.session.delete(wallet)
    db.session.commit()

    return (
        jsonify(
            {
                "status": "success",
                "message": "Wallet deleted successfully",
                "wallet": {
                    "UID": wallet.UID,
                    "amount": wallet.amount,
                },
            }
        ),
        200,
    )


@app.route("/api/v1/wallets", methods=["GET"])
def get_all_wallets():
    """Получает все доступные кошельки"""
    wallets = Wallet.query.all()

    if not wallets:
        return (
            jsonify(
                {"status": "success", "message": "No wallets found", "wallets": []}
            ),
            200,
        )

    wallets_data = [{"UID": wallet.UID, "amount": wallet.amount} for wallet in wallets]

    return jsonify({"status": "success", "wallets": wallets_data}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0")
