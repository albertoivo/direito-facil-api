import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# IMPORTANTE: Definir TESTING antes de qualquer import da aplicação
os.environ["TESTING"] = "True"
os.environ["LOG_LEVEL"] = "ERROR"


def setup_logging():
    # Se estiver em ambiente de teste, usa configuração simples
    if os.getenv("TESTING", False):
        logging.basicConfig(
            level=logging.ERROR,
            format="%(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )
        return logging.getLogger(__name__)

    # Configuração normal para desenvolvimento/produção
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(
                f"logs/app_{datetime.now().strftime('%Y%m%d')}.log",
                encoding="utf-8",
            ),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Sistema de logging configurado com sucesso")
    return logger
