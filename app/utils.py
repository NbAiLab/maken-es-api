import enum
import logging
import os
from typing import Tuple
from typing import Union

from elasticsearch import AsyncElasticsearch
from fastapi.logger import logger as fastapi_logger


class FieldsEnum(enum.Enum):
    filename = "filename"
    vector = "vector"
    id = "id"


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


def scale_hits(hits: list, scale_to: Tuple[Union[float, int]]) -> list:
    """Scale similarity values to be in the range defined by scale_to"""
    similarities = [hit["fields"]["similarity"][0] for hit in hits]
    scale_from = (min(similarities), max(similarities))
    for hit in hits:
        hit["fields"]["scaled"] = [scale_hit(
            hit["fields"]["similarity"][0],
            scale_from=scale_from,
            scale_to=scale_to,
        )]
    return hits


def scale_hit(
    value: float,
    scale_from: Tuple[Union[float, int]],
    scale_to: Tuple[Union[float, int]],
) -> float:
    """Scale one value from the range scale_from to scale_to"""
    scale = (scale_to[1] - scale_to[0]) / (scale_from[1] - scale_from[0])
    capped = min(scale_from[1], max(scale_from[0], value)) - scale_from[0]
    scaled = capped * scale + scale_to[0]
    if isinstance(scale_to[0], int) and isinstance(scale_to[1], int):
        return int(scaled)
    else:
        return scaled
