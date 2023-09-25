from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import uuid4
from models.models import Conversation
from urllib.parse import quote
import logging.config
from logger.logging_config import LOGGING_CONFIG
import httpx
import pybreaker


## Bearer token setup
SECRET_TOKEN = "my_secret_bearer_token"  # I'd store securely in production using env variables or secrets management tools
security = HTTPBearer()

def validate_token(authorization: HTTPAuthorizationCredentials = Depends(security)):
    token = authorization.credentials
    if token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token or unauthorized access")
    return token

### Circuit breaker setup
breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=10
)

### Logging setup
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

app = FastAPI()

MATCHING_SERVICE_URL = "http://answer:8001"
CONVERSATION_SERVICE_URL = "http://conversation:8002"


async def get_answer_from_cache(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONVERSATION_SERVICE_URL}/get_cached_answer?question={question}"
        )
        if response.status_code == 200:
            return response.json()['answer']
        else:
            return None
    

@app.get("/health/")
async def health_check():
    try:
        # dummy method, normally we'd have some proper health checks
        return {"status": "healthy"}
    except:
        raise HTTPException(status_code=500, detail="Service not healthy")
    

@breaker
async def fetch_answer(question: str, token: str):
    async with httpx.AsyncClient(timeout=5.0) as client:
        TOKEN_HEADER = {"Authorization": f"Bearer {SECRET_TOKEN}"}
        response = await client.post(f"{MATCHING_SERVICE_URL}/match_answer/", params={"question": quote(question)}, headers=TOKEN_HEADER)
        logger.info(msg = breaker.current_state)
        response.raise_for_status()  # This will raise an HTTPError if an HTTP error occurs.
        logger.info(msg = response)
        logger.info(msg = breaker.current_state)
        return response.json()

@app.post("/ask/", tags=["Questions"], description="Ask a question and get an answer from the knowledge base.")
async def ask_question(question: str, cached_answer: str = Depends(get_answer_from_cache), token: str = Depends(validate_token)):
    logger.info(msg = breaker.current_state)
    if cached_answer:
        return {"code": 200, "answer": cached_answer}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            TOKEN_HEADER = {"Authorization": f"Bearer {SECRET_TOKEN}"}
            response_with_answer = await fetch_answer(question, token)
            logger.info(msg = breaker.current_state)
            convo = Conversation(user = str(uuid4()), question = question, answer = response_with_answer["answer"])
            response = await client.post(f"{CONVERSATION_SERVICE_URL}/store_conversations/", json = convo.dict(), headers=TOKEN_HEADER)
            # Check for errors while saving the convo
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to store conversation: {response.text}"
                )
            return {"answer": response_with_answer["answer"]}
    except (httpx.HTTPError, pybreaker.CircuitBreakerError) as err:
        # Fallback strategy: return a generic answer
        logger.error(msg=err)
        return {
            "code": 404,
            "answer": "Sorry, I'm unable to fetch an answer right now. Please try again later."}
    except Exception as e:
        logger.error(msg=response)
        logger.info(convo.__repr__)
        logger.info(msg=breaker.current_state)
        return {"code": 500,
            "answer": e}