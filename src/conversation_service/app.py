from fastapi import FastAPI, HTTPException
from typing import List, Tuple
from celery import Celery
from models.models import Conversation
import redis
import hashlib
import ast

import logging.config
from logger.logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Celery
celery_app = Celery('tasks')
celery_app.config_from_object('configs.celery_config')

# Initialize Redis for caching
r = redis.StrictRedis(host='redis', port=6379, db=0, socket_timeout=5)
CACHED_CONVO_LIMIT = 20

@app.get("/health/")
async def health_check():
    try:
        if not r.ping():
            raise Exception("Redis server is unreachable")
        return {"status": "healthy"}
    except:
        raise HTTPException(status_code=500, detail="Service not healthy")
   

@celery_app.task(bind=True, max_retries=3, soft_time_limit=10)
def save_conversation(self, conversation):
    try:
        conversation_str = str(conversation)
               
        r.lpush("conversations", conversation_str)
        r.ltrim("conversations", 0, CACHED_CONVO_LIMIT - 1)
        
        return {"msg": f"{conversation_str} is saved"}
    except redis.RedisError as re:
        logger.error(re)
    except Exception as e:
        logger.info(msg="Retrying to save conversation")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@app.post("/store_conversations/", tags=["Conversations"], description="Save a conversation to the history.")
async def add_conversation(conversation: Conversation):
    task = save_conversation.delay(conversation.dict())
    return {"conversation": conversation, "task_id": task.id}

@app.get("/conversations/", tags=["Conversations"], description="Retrieve the last n conversations from history.")
async def get_conversations(count: int):
    conversations = r.lrange("conversations", 0, count-1)
    logger.info(msg=conversations)
    if not conversations:
        raise HTTPException(status_code=404, detail="Conversations not found")
    return [ast.literal_eval(conversation.decode('utf-8')) for conversation in conversations]

@app.get("/get_cached_answer/", tags=["Cache"], description="Get cached answer based on a question.")
async def get_cached_answer(question: str):
    cached_answer_list = r.lrange("conversations", 0, CACHED_CONVO_LIMIT - 1)
    logger.info(msg=cached_answer_list)
    if cached_answer_list:
        for cached_answer in cached_answer_list:
            logger.info(msg=cached_answer)
            answer = ast.literal_eval(cached_answer.decode('utf-8'))
            if question == answer.get("question"):
                return {"answer": answer.get("answer", "")}
    else:
        return {"code": 404, "answer": ""}
