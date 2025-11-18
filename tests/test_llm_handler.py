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
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm_structured.ainvoke = AsyncMock(
                return_value=LLMAnswerSchema(answer="42")
            )
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            # Create handler and test
            handler = LLMAnswerHandler()
            result = await handler.handle("What is 40 + 2?")

            # Assertions
            assert result == "42"
            mock_llm_structured.ainvoke.assert_called_once()
            call_args = mock_llm_structured.ainvoke.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0]["role"] == "system"
            assert call_args[1]["role"] == "user"
            assert call_args[1]["content"] == "What is 40 + 2?"

    @pytest.mark.asyncio
    async def test_handle_complex_math_question(self):
        """Test handling a complex math question"""
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm_structured.ainvoke = AsyncMock(
                return_value=LLMAnswerSchema(answer="5.0")
            )
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            handler = LLMAnswerHandler()
            result = await handler.handle("What is the square root of 25?")

            assert result == "5.0"
            mock_llm_structured.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_returns_none_when_no_structured_response(self):
        """Test that handler returns None when LLMAnswerSchema has no answer"""
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            # Setup mocks
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            # Return LLMAnswerSchema without answer
            mock_llm_structured.ainvoke = AsyncMock(
                return_value=LLMAnswerSchema(answer=None)
            )
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            handler = LLMAnswerHandler()
            result = await handler.handle("What is 1 + 1?")

            # Should return None from LLMAnswerSchema with no answer
            assert result is None

    @pytest.mark.asyncio
    async def test_handler_initialization_with_correct_settings(self):
        """Test that handler is initialized with correct settings"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.settings") as mock_settings,
        ):
            # Setup settings mock
            mock_settings.default_model = "test-model"
            mock_settings.openai_api_key = "test-api-key"
            mock_settings.default_max_tokens = 1000
            mock_settings.default_temperature = 0.5

            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            # Create handler instance to trigger initialization
            handler = LLMAnswerHandler()
            assert handler is not None

            # Verify ChatOpenAI was called with correct parameters
            mock_chat_openai.assert_called_once_with(
                model="test-model",
                api_key="test-api-key",
                max_tokens=1000,
                temperature=0.5,
            )

            # Verify with_structured_output was called with correct schema
            mock_llm.with_structured_output.assert_called_once_with(
                schema=LLMAnswerSchema
            )

    @pytest.mark.asyncio
    async def test_handler_with_structured_output(self):
        """Test that handler uses with_structured_output method"""
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            # Create handler instance to trigger initialization
            handler = LLMAnswerHandler()
            assert handler is not None

            # Verify with_structured_output was called
            mock_llm.with_structured_output.assert_called_once_with(
                schema=LLMAnswerSchema
            )

            # Verify handler has _llm_with_structured_output attribute
            assert handler._llm_with_structured_output == mock_llm_structured

    @pytest.mark.asyncio
    async def test_get_llm_answer_handler_singleton(self):
        """Test that get_llm_answer_handler returns singleton instance"""
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

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
        with patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai:
            mock_llm = MagicMock()
            mock_llm_structured = MagicMock()
            mock_llm_structured.ainvoke = AsyncMock(
                side_effect=Exception("LLM API error")
            )
            mock_llm.with_structured_output.return_value = mock_llm_structured
            mock_chat_openai.return_value = mock_llm

            handler = LLMAnswerHandler()

            # Should raise the exception
            with pytest.raises(Exception, match="LLM API error"):
                await handler.handle("What is 1 + 1?")
