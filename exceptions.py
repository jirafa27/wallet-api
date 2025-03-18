class WalletError(Exception):
    """Базовый класс исключений для кошелька."""

    def __init__(self, message="Ошибка операции с кошельком"):
        self.message = message
        super().__init__(self.message)


class InsufficientFundsError(WalletError):
    """Ошибка, когда не хватает средств для списания."""

    def __init__(self, message="Недостаточно средств на счете"):
        super().__init__(message)


class InvalidAmountError(WalletError):
    """Ошибка, если передана некорректная сумма."""

    def __init__(self, message="Сумма должна быть положительным числом"):
        super().__init__(message)
