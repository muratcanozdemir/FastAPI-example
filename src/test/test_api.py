import pytest
from fastapi.testclient import TestClient
import httpx

from main.app import main_app  
from answer_match.app import answer_app
from conversation_service.app import conversation_app

@pytest.mark.asyncio
async def test_ask_question():
    # Mocking dependencies
    async def mock_get_answer_from_cache(question: str):
        return None

    async def mock_validate_token(authorization):
        return "valid_token"

    client = TestClient(main_app)
    # Replace the actual dependencies with mocks
    main_app.dependency_overrides[get_answer_from_cache] = mock_get_answer_from_cache
    main_app.dependency_overrides[validate_token] = mock_validate_token

    # Define the request data
    question = "What's the tallest mountain?"

    # Make a request to the API
    response = client.post("/ask/", json={"question": question})

    # Check the response
    assert response.status_code == 200
    assert "answer" in response.json()

def test_store_conversation():
    # Define the request data
    conversation = {
        "user": "some-uuid",
        "question": "What's the tallest mountain?",
        "answer": "Mount Everest"
    }
    client = TestClient(conversation_app)
    # Make a request to the API
    response = client.post("/store_conversations/", json=conversation)

    # Check the response
    assert response.status_code == 200
    assert response.json()["conversation"] == conversation

@pytest.mark.asyncio
async def test_match_answer():
    # Define the request data
    question = "What's the tallest mountain?"
    client = TestClient(answer_app)
    # Make a request to the API
    response = client.post("/match_answer/", json={"question": question})

    # Check the response
    assert response.status_code == 200
    assert "answer" in response.json()
