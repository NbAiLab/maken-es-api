import enum
import logging
import os

from elasticsearch import AsyncElasticsearch
from fastapi.logger import logger as fastapi_logger


class FieldsEnum(enum.Enum):
    filename = "filename"
    vector = "vector"
    urn = "urn"
    identifier = "identifier"


class MetricsEnum(enum.Enum):
    score = "score"
    cosine = "cosine"
    euclidean = "euclidean"


def get_loggers() -> None:
    """Sets loggers to work under gunicorn, uvicorn, and FastAPI"""
    is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
    server_logger = logging.getLogger(
        "gunicorn.error" if is_gunicorn else "uvicorn"
    )
    fastapi_logger.handlers = server_logger.handlers
    if __name__ == "main":
        fastapi_logger.setLevel(logging.DEBUG)
    else:
        fastapi_logger.setLevel(server_logger.level)
    return fastapi_logger


def get_elastic() -> AsyncElasticsearch:
    """Returns an asynchronous Elasticearch client instance"""
    host = os.environ.get("ES_HOST", "localhost")
    port = int(os.environ.get("ES_PORT", 9200))
    user = os.environ.get("ES_USER", "admin")
    password = os.environ.get("ES_PASS", "admin")
    elastic = AsyncElasticsearch(
        [{'host': host, 'port': port}],
        http_auth=(user, password),
        timeout=60, max_retries=200, retry_on_timeout=True,
    )
    return elastic
