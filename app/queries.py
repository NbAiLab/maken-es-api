from typing import List, Optional


COSINE_SIMILARITY = """
double dotProduct = 0.0;
double normA = 0.0;
double normB = 0.0;
for (int i = 0; i < params['_source']['{vector}'].length; i++) {{
  dotProduct += params['_source']['{vector}'][i] * params['vector'][i];
  normA += Math.pow(params['_source']['{vector}'][i], 2);
  normB += Math.pow(params['vector'][i], 2);
}}
return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
""".replace("\n", " ").strip()


def get_by_field(field: str, value: str, vector_field: str="vector") -> dict:
    return {
        "query": {
            "query_string": {
                "query": f"{field}:{value}"
            }
        },
        "_source": vector_field,
            "from": 0,
        "size": 1
    }


def get_similar_by_vector(
    vector: List[float],
    k: int=25,
    size: int=100,
    offset: Optional[int]=None,
    fields: Optional[List[str]]=None,
    filters: Optional[dict]=None,
    vector_field: str="vector",
) -> dict:
    cosine_similarity = COSINE_SIMILARITY.format(vector=vector_field)
    query = {
        "size": size,
        "query": {
            "knn": {
                "vector": {
                    "vector": vector,
                    "k": k
                }
            }
        },
        "script_fields": {
            "similarity": {
                "script": {
                    "lang": "painless",
                    "source": cosine_similarity,
                    "params": {
                        "vector": vector
                    }
                }
            },
        }
    }
    if offset:
        query["from"] = offset
    if fields:
        for field in fields:
            field = field.strip()
            query["script_fields"][field] = {
                "script": {"source": f"params['_source']['{field}']"}
            }
    return query
