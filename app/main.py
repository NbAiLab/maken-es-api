#!/usr/bin/env python
import os
from typing import Optional, Union, List

from fastapi import FastAPI, Response, status
from starlette.responses import RedirectResponse

from .queries import get_by_field, get_similar_by_vector
from .utils import get_elastic, get_loggers, FieldsEnum, MetricsEnum


app = FastAPI(description="""
Maken Elasticsearch API
""")
elastic = get_elastic()
logger = get_loggers()


@app.get("/")
async def root():
    """Redirets to documentation"""
    return RedirectResponse(url="/docs")


@app.post("/similarity/{index}/{field}")
@app.post("/similarity/{index}/{field}/", include_in_schema=False)
async def get_similar(
    value: Union[str, List[float]],
    response: Response,
    index: str="*",
    field: FieldsEnum=FieldsEnum.filename.value,
    size: int=100,
    k: int=25,
    metric: Optional[MetricsEnum]=MetricsEnum.score.value,
    scale: Optional[tuple]=None,
    fields: Optional[str]=None,
) -> list:
    """
    Return up to 'size' similar items to the one specified by 'field' with
    'value' in 'index'. Results can also be scaled to range from 'scale[0]' to
    'scale[1]'. And if needed, only fields in 'fields' will be returned
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
        fields=fields.split(",") if fields else [],
        filters=None
    )
    results = await elastic.search(body=body, index=index)
    return results["hits"]["hits"][1:]  # first match is always the query item


@app.get("/random/{index}")
@app.get("/random/{index}/", include_in_schema=False)
async def get_random_set(index: str="*", fields: Optional[str]=None) -> list:
    """Extract a random set of elements for the specified index"""
    random_query = {
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

