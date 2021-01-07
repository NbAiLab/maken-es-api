#!/usr/bin/env python
import os
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from fastapi import FastAPI
from fastapi import Response
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from .queries import get_by_field
from .queries import get_similar_by_vector
from .utils import get_elastic
from .utils import get_loggers
from .utils import get_root_path
from .utils import scale_hits
from .utils import FieldsEnum
from .utils import MetricsEnum
from .utils import ScalesEnum


app = FastAPI(root_path=get_root_path(), title="Maken", description="""
Maken Elasticsearch API
""")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
elastic = get_elastic()
logger = get_loggers()


@app.get("/")
async def root():
    """Redirets to documentation"""
    return RedirectResponse(url=f"{get_root_path()}/docs")


@app.post("/similarity/{index}/{field}")
@app.post("/similarity/{index}/{field}/", include_in_schema=False)
async def get_similar(
    value: Union[str, List[float]],
    response: Response,
    index: str="*",
    field: FieldsEnum=FieldsEnum.filename.value,
    size: int=100,
    offset: Optional[int]=None,
    k: int=25,
    metric: Optional[MetricsEnum]=MetricsEnum.cosine.value,
    scale_to: Optional[Tuple[int, int]]=None,
    scale_from: Optional[Tuple[float, Union[float, ScalesEnum]]]=None,
    fields: Optional[str]=None,
    filters: Optional[Dict[str, str]]=None,
) -> list:
    """
    Return up to 'size' similar items to the one specified by 'field' with
    'value' in 'index'. Results can also be scaled to range from 'scale_to[0]' to
    'scale_to[1]'. And if needed, only fields in 'fields' will be returned
    """
    if field != FieldsEnum.vector:
        results = await elastic.search(
            q=f"{field.value}:{value}", index=index, _source=["vector"], size=1
        )
        if results["hits"]["hits"]:
            vector = results["hits"]["hits"][0]["_source"]["vector"]
        else:
            response.status_code = status.HTTP_404_NOT_FOUND
            return {"error": f"Not found {field.value}={value} on {index}"}
    body = get_similar_by_vector(
        vector,
        k=k,
        size=size + 1,
        offset=offset,
        fields=fields.split(",") if fields else [],
        filters=filters
    )
    results = await elastic.search(body=body, index=index)
    hits = sorted(
        results["hits"]["hits"][1:],  # first match is always the query item
        key=lambda x: x["fields"]["similarity"][0],
        reverse=True,
    )
    if scale_to:
        return scale_hits(hits, scale_to=scale_to, scale_from=scale_from)
    else:
        return hits


@app.get("/random/{index}")
@app.get("/random/{index}/", include_in_schema=False)
async def get_random_set(
    index: str="*",
    size: Optional[int]=20,
    fields: Optional[str]=None,
) -> list:
    """Extract a random set of elements for the specified index"""
    random_query = {
        "size": size,
        "query": {
            "function_score": {
                "random_score": {"field": "_seq_no"}
            }
        }
    }
    if fields is not None:
        random_query["_source"] = [
            field.strip() for field in fields.split(",")
        ]
    response = await elastic.search(index=index, body=random_query)
    return response['hits']['hits']

