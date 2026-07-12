import logging
from app.services.copilot_orchestrator import CopilotOrchestrator

logger = logging.getLogger(__name__)

class ChatService:

    @staticmethod
    async def process_chat_message(session_id: str, user_id: str, workspace_id: str, message: str) -> str:
        """
        Processes a user message by delegating to CopilotOrchestrator.
        """
        try:
            result = await CopilotOrchestrator.answer(
                workspace_id=workspace_id,
                user_id=user_id,
                message=message,
                session_id=session_id
            )
            return result.get("answer", "I encountered an error generating an answer.")
        except Exception as e:
            logger.error(f"ChatService delegation failed: {e}")
            return "I encountered a cognitive error while processing your request. Please try again."
