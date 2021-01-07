import enum
import logging
import os
from typing import Tuple
from typing import Optional
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


class ScalesEnum(enum.Enum):
    max = "max"
    min = "min"


def is_gunicorn() -> bool:
    """Checks whether the API is running under gunicorn"""
    return "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")


def get_root_path() -> str:
    return os.environ.get("ASGI_ROOT_PATH", "/maken" if is_gunicorn() else "")


def get_loggers() -> None:
    """Sets loggers to work under gunicorn, uvicorn, and FastAPI"""
    server_logger = logging.getLogger(
        "gunicorn.error" if is_gunicorn() else "uvicorn"
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
    timeout = int(os.environ.get("ES_TIMEOUT", 60))
    max_retries = int(os.environ.get("ES_MAX_RETRIES", 300))
    elastic = AsyncElasticsearch(
        [{'host': host, 'port': port}],
        http_auth=(user, password),
        timeout=timeout, max_retries=max_retries, retry_on_timeout=True,
    )
    return elastic


def scale_hits(
    hits: list,
    scale_to: Tuple[Union[float, int]],
    scale_from: Optional[Tuple[Union[float, int, ScalesEnum]]]=None,
) -> list:
    """Scale similarity values to be in the range defined by scale_to"""
    similarities = [hit["fields"]["similarity"][0] for hit in hits]
    if scale_from is None:
        scale_from = (min(similarities), max(similarities))
    if scale_from[0] == ScalesEnum.min:
        scale_from = (min(similarities), scale_from[1])
    if scale_from[1] == ScalesEnum.max:
        scale_from = (scale_from[0], max(similarities))
    for hit in hits:
        hit["fields"]["scaled"] = [scale_hit(
            hit["fields"]["similarity"][0],
            scale_to=scale_to,
            scale_from=scale_from,
        )]
    return hits


def scale_hit(
    value: float,
    scale_to: Tuple[Union[float, int]],
    scale_from: Tuple[Union[float, int]],
) -> float:
    """Scale one value from the range scale_from to scale_to"""
    if scale_from[1] == scale_from[0]:
        # Edge case when number of values is 1
        return scale_to[0]
    scale = (scale_to[1] - scale_to[0]) / (scale_from[1] - scale_from[0])
    capped = min(scale_from[1], max(scale_from[0], value)) - scale_from[0]
    scaled = capped * scale + scale_to[0]
    if isinstance(scale_to[0], int) and isinstance(scale_to[1], int):
        return int(scaled)
    else:
        return scaled
