import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.api.v1.answers.handlers import LLMAnswerHandler, get_llm_answer_handler
from src.api.v1.answers.schemas import LLMAnswerSchema


class TestLLMAnswerHandler:
    """Tests for LLMAnswerHandler with mocked LLM"""

    @pytest.mark.asyncio
    async def test_handle_simple_math_question(self):
        """Test handling a simple math question with mocked LLM"""
        # Create handler instance
        with patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()

            # Create mock response structure
            mock_message = MagicMock()
            mock_message.parsed = LLMAnswerSchema(answer="42")
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]

            mock_completions.parse = AsyncMock(return_value=mock_response)
            mock_chat.completions = mock_completions
            mock_llm.chat = mock_chat
            mock_async_openai.return_value = mock_llm

            # Create handler and test
            handler = LLMAnswerHandler()
            result = await handler.handle("What is 40 + 2?")

            # Assertions
            assert result == "42"
            mock_completions.parse.assert_called_once()
            call_kwargs = mock_completions.parse.call_args.kwargs
            assert call_kwargs["response_format"] == LLMAnswerSchema
            assert len(call_kwargs["messages"]) == 2
            assert call_kwargs["messages"][0]["role"] == "system"
            assert call_kwargs["messages"][1]["role"] == "user"
            assert call_kwargs["messages"][1]["content"] == "What is 40 + 2?"

    @pytest.mark.asyncio
    async def test_handle_complex_math_question(self):
        """Test handling a complex math question"""
        with patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()

            mock_message = MagicMock()
            mock_message.parsed = LLMAnswerSchema(answer="5.0")
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]

            mock_completions.parse = AsyncMock(return_value=mock_response)
            mock_chat.completions = mock_completions
            mock_llm.chat = mock_chat
            mock_async_openai.return_value = mock_llm

            handler = LLMAnswerHandler()
            result = await handler.handle("What is the square root of 25?")

            assert result == "5.0"
            mock_completions.parse.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_returns_none_when_no_structured_response(self):
        """Test that handler returns None when LLMAnswerSchema has no answer"""
        with patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()

            mock_message = MagicMock()
            mock_message.parsed = LLMAnswerSchema(answer=None)
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]

            mock_completions.parse = AsyncMock(return_value=mock_response)
            mock_chat.completions = mock_completions
            mock_llm.chat = mock_chat
            mock_async_openai.return_value = mock_llm

            handler = LLMAnswerHandler()
            result = await handler.handle("What is 1 + 1?")

            # Should return None from LLMAnswerSchema with no answer
            assert result is None

    @pytest.mark.asyncio
    async def test_handler_initialization_with_correct_settings(self):
        """Test that handler is initialized with correct settings"""
        with (
            patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai,
            patch("src.api.v1.answers.handlers.settings") as mock_settings,
        ):
            # Setup settings mock
            mock_settings.openai_api_key = "test-api-key"

            mock_llm = MagicMock()
            mock_async_openai.return_value = mock_llm

            # Create handler instance to trigger initialization
            handler = LLMAnswerHandler()
            assert handler is not None

            # Verify AsyncOpenAI was called with correct parameters
            mock_async_openai.assert_called_once_with(
                api_key="test-api-key",
            )

    @pytest.mark.asyncio
    async def test_get_llm_answer_handler_singleton(self):
        """Test that get_llm_answer_handler returns singleton instance"""
        with patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai:
            mock_llm = MagicMock()
            mock_async_openai.return_value = mock_llm

            # Clear the cache first
            get_llm_answer_handler.cache_clear()

            # Get handler twice
            handler1 = get_llm_answer_handler()
            handler2 = get_llm_answer_handler()

            # Should be the same instance
            assert handler1 is handler2

    @pytest.mark.asyncio
    async def test_handle_with_exception(self):
        """Test handling when LLM raises an exception"""
        with patch("src.api.v1.answers.handlers.AsyncOpenAI") as mock_async_openai:
            mock_llm = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()
            mock_completions.parse = AsyncMock(side_effect=Exception("LLM API error"))
            mock_chat.completions = mock_completions
            mock_llm.chat = mock_chat
            mock_async_openai.return_value = mock_llm

            handler = LLMAnswerHandler()

            # Should raise the exception
            with pytest.raises(Exception, match="LLM API error"):
                await handler.handle("What is 1 + 1?")
