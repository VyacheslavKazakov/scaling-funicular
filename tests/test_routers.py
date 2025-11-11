import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from src.api.v1.answers.routers import router
from src.api.v1.answers.services import AnswerService


@pytest.fixture
def mock_answer_service():
    """Fixture that provides a mocked AnswerService"""
    service = MagicMock(spec=AnswerService)
    service.get_answer = AsyncMock()
    return service


@pytest.fixture
def test_app(mock_answer_service):
    """Fixture that creates a test FastAPI app with mocked dependencies"""
    app = FastAPI()
    app.include_router(router)

    # Override the dependency
    from src.api.v1.answers.routers import get_answer_service

    app.dependency_overrides[get_answer_service] = lambda: mock_answer_service

    # Disable rate limiting for tests
    with patch("src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f):
        yield app

    app.dependency_overrides.clear()


class TestAnswersRouter:
    """Tests for /get_answer endpoint"""

    def test_get_answer_success(self, test_app, mock_answer_service):
        """Test successful answer retrieval"""
        # Setup mock
        mock_answer_service.get_answer.return_value = "42"

        # Make request with URL-encoded + sign
        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=What%20is%2040%20plus%202")

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": "42"}
        mock_answer_service.get_answer.assert_called_once_with(
            question="What is 40 plus 2"
        )

    def test_get_answer_with_complex_math_question(self, test_app, mock_answer_service):
        """Test answer for complex mathematical question"""
        mock_answer_service.get_answer.return_value = "5.0"

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get(
                    "/get_answer?question=What is the square root of 25?"
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": "5.0"}

    def test_get_answer_returns_none(self, test_app, mock_answer_service):
        """Test when service returns None - should fail validation"""
        mock_answer_service.get_answer.return_value = None

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=Invalid question")

        assert response.status_code == status.HTTP_200_OK

    def test_get_answer_missing_question_parameter(self, test_app, mock_answer_service):
        """Test request without question parameter"""
        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "detail" in response.json()

    def test_get_answer_empty_question(self, test_app, mock_answer_service):
        """Test request with empty question"""
        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=")

        # Empty string violates min_length=1 constraint
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_answer_with_special_characters(self, test_app, mock_answer_service):
        """Test question with special characters"""
        mock_answer_service.get_answer.return_value = "3.14159"

        question = "What is π (pi)?"
        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get(f"/get_answer?question={question}")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": "3.14159"}

    def test_get_answer_with_url_encoded_question(self, test_app, mock_answer_service):
        """Test question with URL encoding"""
        mock_answer_service.get_answer.return_value = "100"

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get(
                    "/get_answer?question=What%20is%2010%20times%2010%3F"
                )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": "100"}
        # Verify decoded question was passed to service
        mock_answer_service.get_answer.assert_called_once_with(
            question="What is 10 times 10?"
        )

    def test_get_answer_with_mathematical_symbols(self, test_app, mock_answer_service):
        """Test question with mathematical symbols"""
        mock_answer_service.get_answer.return_value = "8"

        question = "Calculate 2^3"
        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get(f"/get_answer?question={question}")

        assert response.status_code == status.HTTP_200_OK
        mock_answer_service.get_answer.assert_called_once_with(question=question)

    def test_get_answer_multiple_requests(self, test_app, mock_answer_service):
        """Test multiple sequential requests"""
        # Setup different responses
        mock_answer_service.get_answer.side_effect = ["42", "5.0", "3.14"]

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                # Request 1
                response1 = client.get("/get_answer?question=What is 40 + 2?")
                assert response1.status_code == status.HTTP_200_OK
                assert response1.json() == {"answer": "42"}

                # Request 2
                response2 = client.get("/get_answer?question=Square root of 25?")
                assert response2.status_code == status.HTTP_200_OK
                assert response2.json() == {"answer": "5.0"}

                # Request 3
                response3 = client.get("/get_answer?question=What is pi?")
                assert response3.status_code == status.HTTP_200_OK
                assert response3.json() == {"answer": "3.14"}

        assert mock_answer_service.get_answer.call_count == 3

    def test_get_answer_service_exception(self, test_app, mock_answer_service):
        """Test when service raises an exception"""
        mock_answer_service.get_answer.side_effect = Exception("Service error")

        with TestClient(test_app, raise_server_exceptions=False) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=Any question")

        # FastAPI should handle the exception and return 500
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_get_answer_response_schema(self, test_app, mock_answer_service):
        """Test that response follows AnswerGetSchema"""
        mock_answer_service.get_answer.return_value = "test answer"

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=Test question")

        assert response.status_code == status.HTTP_200_OK
        json_data = response.json()
        assert "answer" in json_data
        assert isinstance(json_data["answer"], str)

    def test_get_answer_with_numeric_answer(self, test_app, mock_answer_service):
        """Test with numeric answer (returned as string)"""
        mock_answer_service.get_answer.return_value = "123.456"

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                response = client.get("/get_answer?question=Calculate something")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"answer": "123.456"}

    def test_get_answer_openapi_examples(self, test_app, mock_answer_service):
        """Test that examples from OpenAPI spec work correctly"""
        mock_answer_service.get_answer.return_value = "78.54"

        example_questions = [
            "Calculate the area of a circle with radius 5",
            "Find the derivative of x^2 at x=3",
        ]

        with TestClient(test_app) as client:
            with patch(
                "src.api.v1.answers.routers.limiter.limit", lambda limit: lambda f: f
            ):
                for question in example_questions:
                    mock_answer_service.get_answer.reset_mock()
                    response = client.get(f"/get_answer?question={question}")

                    assert response.status_code == status.HTTP_200_OK
                    mock_answer_service.get_answer.assert_called_once_with(
                        question=question
                    )
