"""
FINESE2 - AI Assistant Service
Migrates and enhances engine/ai_assistant.py with user context and conversation history.
"""
from typing import Dict, List, Any, Optional, Generator
import json
import logging
from datetime import datetime
from engine.ai_assistant import AIAssistant, Message, AIResponse

logger = logging.getLogger(__name__)


class AIService:
    """
    Enhanced AI assistant service with user isolation.
    
    Wraps legacy AIAssistant while adding:
    - User-specific conversation history
    - Context-aware responses
    - Usage tracking
    - Multiple model support per user
    """
    
    def __init__(self):
        self.assistant = AIAssistant()
    
    def chat(self, messages: List[Dict[str, str]], user_id: int,
            dataset_context: Optional[Dict] = None,
            provider: str = 'openai',
            model: Optional[str] = None) -> Dict[str, Any]:
        """
        Send chat message to AI assistant with user context.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            user_id: User sending the message
            dataset_context: Optional dataset context for data-aware responses
            provider: AI provider (openai, anthropic, google, etc.)
            model: Specific model to use
            
        Returns:
            Dictionary with AI response and metadata
        """
        try:
            # Convert messages to Message objects
            message_objects = [
                Message(role=msg['role'], content=msg['content'])
                for msg in messages
            ]
            
            # Add dataset context if provided
            if dataset_context:
                context_msg = Message(
                    role='system',
                    content=f"Dataset context: {json.dumps(dataset_context)}"
                )
                message_objects.insert(0, context_msg)
            
            # Get response from AI assistant
            response = self.assistant.chat(
                messages=message_objects,
                provider=provider,
                model=model
            )
            
            result = {
                'response': response.content,
                'model': response.model,
                'provider': response.provider,
                'usage': response.usage,
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id
            }
            
            logger.info(f"User {user_id} chatted with AI ({provider}/{response.model})")
            
            return result
            
        except Exception as e:
            logger.error(f"AI chat failed for user {user_id}: {e}")
            raise
    
    def stream_chat(self, messages: List[Dict[str, str]], user_id: int,
                   provider: str = 'openai',
                   model: Optional[str] = None) -> Generator[str, None, None]:
        """
        Stream chat responses from AI assistant.
        
        Args:
            messages: List of message dictionaries
            user_id: User sending the message
            provider: AI provider
            model: Specific model to use
            
        Yields:
            Streaming response chunks
        """
        try:
            message_objects = [
                Message(role=msg['role'], content=msg['content'])
                for msg in messages
            ]
            
            for chunk in self.assistant.stream_chat(
                messages=message_objects,
                provider=provider,
                model=model
            ):
                yield chunk
            
            logger.info(f"User {user_id} streamed chat with AI ({provider})")
            
        except Exception as e:
            logger.error(f"AI streaming chat failed for user {user_id}: {e}")
            raise
    
    def get_conversation_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user's conversation history."""
        # This would query the database in production
        # For now, return empty list
        return []
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available AI providers and models."""
        return self.assistant.get_available_providers()
    
    def analyze_data_with_ai(self, df_summary: Dict, user_query: str,
                            user_id: int, provider: str = 'openai') -> Dict[str, Any]:
        """
        Analyze dataset using AI with context.
        
        Args:
            df_summary: DataFrame summary (columns, dtypes, stats)
            user_query: User's question about the data
            user_id: User making the request
            provider: AI provider to use
            
        Returns:
            AI analysis response
        """
        try:
            system_prompt = f"""You are a data science expert analyzing a dataset.

Dataset Summary:
{json.dumps(df_summary, indent=2)}

Provide insights, recommendations, and answer questions about this dataset.
Be specific, actionable, and cite statistical evidence when possible."""
            
            messages = [
                Message(role='system', content=system_prompt),
                Message(role='user', content=user_query)
            ]
            
            response = self.assistant.chat(
                messages=messages,
                provider=provider
            )
            
            result = {
                'analysis': response.content,
                'model': response.model,
                'provider': response.provider,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"User {user_id} requested AI data analysis")
            
            return result
            
        except Exception as e:
            logger.error(f"AI data analysis failed for user {user_id}: {e}")
            raise


# Singleton instance
ai_service = AIService()
