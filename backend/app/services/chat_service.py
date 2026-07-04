import logging
from datetime import datetime, UTC
from typing import List, Dict
from app.models.chat import ChatSession
from app.services.llm_service import LLMService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStoreService
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatService:

    @staticmethod
    async def process_chat_message(session_id: str, user_id: str, workspace_id: str, message: str) -> str:
        """
        Processes a user message through a RAG pipeline (Retrieval-Augmented Generation).
        """
        # Fetch or create session
        session = await ChatSession.get(session_id)
        if not session:
            session = ChatSession(
                id=session_id, # Can use provided ID if needed, or let MongoDB assign
                user_id=user_id,
                workspace_id=workspace_id,
                messages=[]
            )
            await session.insert()
            
        # 1. Store User Message
        session.messages.append({"role": "user", "content": message})
        
        # 2. Retrieve Context from Qdrant
        context_text = ""
        try:
            query_embeddings = await EmbeddingService.get_embeddings([message])
            if query_embeddings:
                collection = settings.QDRANT_COLLECTION_NAME or "documents_general"
                results = await VectorStoreService.search_workspace(
                    collection_name=collection,
                    workspace_id=workspace_id,
                    query_vector=query_embeddings[0],
                    limit=5
                )
                
                # Format context
                if results:
                    context_chunks = []
                    for res in results:
                        title = res.get("title", "Unknown Source")
                        text = res.get("text", "")
                        context_chunks.append(f"--- SOURCE: {title} ---\n{text}\n")
                    context_text = "\n".join(context_chunks)
        except Exception as e:
            logger.error(f"RAG Retrieval failed: {e}")

        # 3. Build System Prompt with Context
        system_prompt = (
            "You are an AI Operational Assistant. You act as the 'Company Brain'.\n"
            "Answer the user's questions strictly based on the provided CONTEXT from the company's internal documents.\n"
            "If the answer is not in the context, say 'I cannot find the answer in the uploaded company documents.'\n"
            "ALWAYS cite your sources by mentioning the SOURCE title in your response.\n\n"
            f"=== CONTEXT ===\n{context_text}\n==============="
        )
        
        messages_to_send = [{"role": "system", "content": system_prompt}]
        
        # Add recent history (last 6 messages) for memory
        recent_history = session.messages[-6:]
        messages_to_send.extend(recent_history)
        
        # 4. Generate AI Response
        try:
            ai_response = await LLMService.generate_chat(messages_to_send, temperature=0.3)
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            ai_response = "I encountered a cognitive error while processing your request. Please try again."
            
        # 5. Store AI Response
        session.messages.append({"role": "assistant", "content": ai_response})
        session.updated_at = datetime.now(UTC)
        await session.save()
        
        return ai_response
