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
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
        ):
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            mock_agent.ainvoke = AsyncMock(
                return_value={
                    "structured_response": LLMAnswerSchema(answer="42"),
                    "messages": [],
                }
            )
            mock_create_agent.return_value = mock_agent

            # Create handler and test
            handler = LLMAnswerHandler()
            result = await handler.handle("What is 40 + 2?")

            # Assertions
            assert result == "42"
            mock_agent.ainvoke.assert_called_once()
            call_args = mock_agent.ainvoke.call_args[0][0]
            assert "messages" in call_args
            assert len(call_args["messages"]) == 2
            assert call_args["messages"][0]["role"] == "system"
            assert call_args["messages"][1]["role"] == "user"
            assert call_args["messages"][1]["content"] == "What is 40 + 2?"

    @pytest.mark.asyncio
    async def test_handle_complex_math_question(self):
        """Test handling a complex math question"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
        ):
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            mock_agent.ainvoke = AsyncMock(
                return_value={
                    "structured_response": LLMAnswerSchema(answer="5.0"),
                    "messages": [],
                }
            )
            mock_create_agent.return_value = mock_agent

            handler = LLMAnswerHandler()
            result = await handler.handle("What is the square root of 25?")

            assert result == "5.0"
            mock_agent.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_returns_none_when_no_structured_response(self):
        """Test that handler returns None when no structured_response"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
        ):
            # Setup mocks
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            # Return dict without structured_response
            mock_agent.ainvoke = AsyncMock(return_value={"messages": []})
            mock_create_agent.return_value = mock_agent

            handler = LLMAnswerHandler()
            result = await handler.handle("What is 1 + 1?")

            # Should return None from default LLMAnswerSchema()
            assert result is None

    @pytest.mark.asyncio
    async def test_handler_initialization_with_correct_settings(self):
        """Test that handler is initialized with correct settings"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
            patch("src.api.v1.answers.handlers.settings") as mock_settings,
        ):
            # Setup settings mock
            mock_settings.default_model = "test-model"
            mock_settings.openai_api_key = "test-api-key"
            mock_settings.default_max_tokens = 1000
            mock_settings.default_temperature = 0.5
            mock_settings.debug = True

            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent

            # Create handler instance to trigger initialization
            handler = LLMAnswerHandler()
            assert handler is not None

            # Verify ChatOpenAI was called with correct parameters
            mock_chat_openai.assert_called_once_with(
                model="test-model",
                api_key="test-api-key",
                temperature=0.5,
            )

            # Verify create_agent was called with correct parameters
            mock_create_agent.assert_called_once()
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs["model"] == mock_llm
            assert call_kwargs["response_format"] == LLMAnswerSchema
            assert call_kwargs["debug"] is True

    @pytest.mark.asyncio
    async def test_handler_with_tools(self):
        """Test that handler is created with safe_execute_code_tool"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
        ):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent

            # Create handler instance to trigger initialization
            handler = LLMAnswerHandler()
            assert handler is not None

            # Verify tools were passed to create_agent
            call_kwargs = mock_create_agent.call_args[1]
            assert "tools" in call_kwargs
            tools = call_kwargs["tools"]
            assert len(tools) == 1
            # The tool should have a name attribute
            assert hasattr(tools[0], "name") or callable(tools[0])

    @pytest.mark.asyncio
    async def test_get_llm_answer_handler_singleton(self):
        """Test that get_llm_answer_handler returns singleton instance"""
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI"),
            patch("src.api.v1.answers.handlers.create_agent"),
        ):
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
        with (
            patch("src.api.v1.answers.handlers.ChatOpenAI") as mock_chat_openai,
            patch("src.api.v1.answers.handlers.create_agent") as mock_create_agent,
        ):
            mock_llm = MagicMock()
            mock_chat_openai.return_value = mock_llm

            mock_agent = MagicMock()
            mock_agent.ainvoke = AsyncMock(side_effect=Exception("LLM API error"))
            mock_create_agent.return_value = mock_agent

            handler = LLMAnswerHandler()

            # Should raise the exception
            with pytest.raises(Exception, match="LLM API error"):
                await handler.handle("What is 1 + 1?")
