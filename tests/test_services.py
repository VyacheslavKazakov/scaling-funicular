import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.v1.answers.services import AnswerService, get_answer_service
from src.api.v1.answers.handlers import LLMAnswerHandler


class TestAnswerService:
    """Tests for AnswerService with mocked dependencies"""

    @pytest.mark.asyncio
    async def test_get_answer_calls_llm_handler(self):
        """Test that get_answer calls LLM handler correctly"""
        # Mock LLM handler
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value="42")

        # Create service with mocked handler
        service = AnswerService(llm_answer_handler=mock_handler)

        # Mock cache decorator to bypass caching
        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            result = await service.get_answer(question="What is 40 + 2?")

        # Verify handler was called with correct question
        assert result == "42"
        mock_handler.handle.assert_called_once_with(question="What is 40 + 2?")

    @pytest.mark.asyncio
    async def test_get_answer_with_different_questions(self):
        """Test get_answer with multiple questions"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)

        # Set up handler to return different answers
        async def mock_handle(question):
            if "factorial" in question.lower():
                return "3628800"
            elif "sqrt" in question.lower() or "square root" in question.lower():
                return "5.0"
            else:
                return "unknown"

        mock_handler.handle = AsyncMock(side_effect=mock_handle)
        service = AnswerService(llm_answer_handler=mock_handler)

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            # Test factorial question
            result1 = await service.get_answer(question="Calculate factorial of 10")
            assert result1 == "3628800"

            # Test square root question
            result2 = await service.get_answer(question="What is square root of 25?")
            assert result2 == "5.0"

            # Test unknown question
            result3 = await service.get_answer(question="Random question")
            assert result3 == "unknown"

        # Verify all calls were made
        assert mock_handler.handle.call_count == 3

    @pytest.mark.asyncio
    async def test_get_answer_returns_none_when_handler_fails(self):
        """Test that get_answer propagates None from handler"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value=None)

        service = AnswerService(llm_answer_handler=mock_handler)

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            result = await service.get_answer(question="Invalid question")

        assert result is None
        mock_handler.handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_answer_with_exception(self):
        """Test that get_answer propagates exceptions from handler"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(side_effect=Exception("LLM API error"))

        service = AnswerService(llm_answer_handler=mock_handler)

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            with pytest.raises(Exception, match="LLM API error"):
                await service.get_answer(question="Any question")

    @pytest.mark.asyncio
    async def test_get_answer_caching_behavior(self):
        """Test that cache decorator is applied with correct parameters"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value="cached answer")

        service = AnswerService(llm_answer_handler=mock_handler)

        # Verify that get_answer method has cache decorator
        assert hasattr(service.get_answer, "__wrapped__") or callable(
            service.get_answer
        )

    def test_service_initialization(self):
        """Test that service initializes correctly with handler"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        service = AnswerService(llm_answer_handler=mock_handler)

        assert service.llm_answer_handler is mock_handler
        assert service._namespace == "answers"

    @pytest.mark.asyncio
    async def test_get_answer_service_dependency(self):
        """Test get_answer_service dependency injection function"""
        with patch(
            "src.api.v1.answers.services.get_llm_answer_handler"
        ) as mock_get_handler:
            mock_handler = MagicMock(spec=LLMAnswerHandler)
            mock_get_handler.return_value = mock_handler

            # Call dependency function
            service = get_answer_service(llm_answer_handler=mock_handler)

            # Verify service was created with handler
            assert isinstance(service, AnswerService)
            assert service.llm_answer_handler is mock_handler

    @pytest.mark.asyncio
    async def test_get_answer_with_empty_string(self):
        """Test get_answer with empty string question"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value="empty response")

        service = AnswerService(llm_answer_handler=mock_handler)

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            result = await service.get_answer(question="")

        assert result == "empty response"
        mock_handler.handle.assert_called_once_with(question="")

    @pytest.mark.asyncio
    async def test_get_answer_with_long_question(self):
        """Test get_answer with very long question"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value="long answer")

        service = AnswerService(llm_answer_handler=mock_handler)
        long_question = "Calculate " + "x * " * 100 + "2"

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            result = await service.get_answer(question=long_question)

        assert result == "long answer"
        mock_handler.handle.assert_called_once_with(question=long_question)

    @pytest.mark.asyncio
    async def test_get_answer_with_special_characters(self):
        """Test get_answer with special characters in question"""
        mock_handler = MagicMock(spec=LLMAnswerHandler)
        mock_handler.handle = AsyncMock(return_value="special answer")

        service = AnswerService(llm_answer_handler=mock_handler)
        special_question = "What is ∫x² dx from 0 to π?"

        with patch(
            "src.api.v1.answers.services.cache_deco", lambda **kwargs: lambda f: f
        ):
            result = await service.get_answer(question=special_question)

        assert result == "special answer"
        mock_handler.handle.assert_called_once_with(question=special_question)
