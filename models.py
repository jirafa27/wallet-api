import random
import string

from flask_sqlalchemy import SQLAlchemy

from exceptions import InvalidAmountError, InsufficientFundsError

db = SQLAlchemy()


def generate_uid():
    """Генерирует случайную строку из 10 символов."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=10))


class Wallet(db.Model):
    __tablename__ = "wallets"

    UID = db.Column(db.String(10), primary_key=True, default=generate_uid)
    amount = db.Column(db.Float, nullable=False, default=0.0)

    def __init__(self):
        self.UID = generate_uid()
        self.amount = 0.0

    def to_dict(self):
        """Конвертирует объект в словарь для JSON-ответа."""
        return {"UID": self.UID, "amount": self.amount}

    def deposit(self, amount):
        """Пополняет кошелек на указанную сумму"""
        if amount <= 0:
            raise InvalidAmountError()
        self.amount += amount
        db.session.commit()

    def withdraw(self, amount):
        """Списывает деньги на указанную сумму, если достаточно средств"""
        if amount <= 0:
            raise InvalidAmountError()

        if amount > self.amount:
            raise InsufficientFundsError()

        self.amount -= amount
        db.session.commit()
