from fastapi import FastAPI, HTTPException
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection, ElasticsearchException
from typing import List, Dict
import logging.config
from logger.logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

ES_HOST = "http://elasticsearch:9200"
INDEX_NAME = "knowledge_base"

es = Elasticsearch([ES_HOST],
    connection_class=RequestsHttpConnection,
    timeout=10,  
    max_retries=15,  
    retry_on_timeout=True)

if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, ignore=400)


@app.get("/health/")
async def health_check():
    try:
        # dummy method, normally we'd have some proper health checks
        return {"status": "healthy"}
    except:
        raise HTTPException(status_code=500, detail="Service not healthy")

@app.post("/populate_data/")
async def populate_data(data: List[Dict[str, str]]):
    actions = [
        {
            "_op_type": "index",
            "_index": INDEX_NAME,
            "_source": item
        }
        for item in data
    ]
    helpers.bulk(es, actions)
    return {"status": "data indexed"}

@app.post("/match_answer/", tags=["Matching"], description="Match a user's question with the best possible answer from the knowledge base.")
async def match_answer(question: str) -> dict:
    body = {
        "query": {
            "match": {
                "question": question
            }
        }
    }
    try: 
        response = es.search(index=INDEX_NAME, body=body)
        if response["hits"]["hits"]:
            return {"answer": response["hits"]["hits"][0]["_source"]["answer"]}
        else:
            return {"answer": "Sorry, I couldn't find an answer to your question."}
    except ElasticsearchException as e:
        return {"answer": "There was an issue fetching the answer. Please try again later."}
