"""Erros de domínio com código HTTP para mapeamento nas rotas."""


class Error(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status