import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address


def get_identifier(request):
    """
    Função para identificar requests únicos.
    Em ambiente de teste, usa um identificador que permite mais requests.
    """
    if os.getenv("TESTING", False):
        return "test-unlimited"  # Identificador especial para testes
    return get_remote_address(request)


# Configuração diferente para teste vs produção
if os.getenv("TESTING", False):
    # Em testes: limites muito altos
    limiter = Limiter(key_func=get_identifier, default_limits=["10000/minute"])
else:
    # Em produção: limites normais
    limiter = Limiter(key_func=get_identifier)


def conditional_limit(rate: str):
    """
    Aplica rate limiting apenas se não estiver em ambiente de teste.
    """

    def decorator(func):
        if os.getenv("TESTING", False):
            # Em testes, retorna a função original sem decorar
            return func
        else:
            # Em produção, aplica o rate limiting
            return limiter.limit(rate)(func)

    return decorator


# Exporta o handler para ser usado no main.py
__all__ = ["limiter", "_rate_limit_exceeded_handler", "conditional_limit"]
