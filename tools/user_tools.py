"""User preference tools - simplified without Redis."""
from typing import Annotated
import logging

logger = logging.getLogger(__name__)

# In-memory storage for preferences (per-user)
_user_preferences = {}


def create_remember_preference_for_user(user_name: str):
    """Create a remember_preference function bound to a specific user."""
    
    # Initialize preferences list for this user
    if user_name not in _user_preferences:
        _user_preferences[user_name] = []
    
    async def remember_preference(
        preference: Annotated[str, "The preference to remember for this user"]
    ) -> str:
        """
        Store a new preference for the current user in memory.
        This allows the agent to learn new preferences during conversations.
        Note: Preferences are only stored for the current session.
        
        Args:
            preference: The preference text to remember
            
        Returns:
            Confirmation message
        """
        try:
            _user_preferences[user_name].append(preference)
            logger.info(f"Stored new preference for {user_name}: {preference}")
            return f"✅ I'll remember that: {preference}"
            
        except Exception as e:
            logger.error(f"Failed to store preference: {e}", exc_info=True)
            return f"❌ Sorry, I couldn't store that preference: {str(e)}"
    
    # Set function name for the agent framework
    remember_preference.__name__ = "remember_preference"
    return remember_preference


def get_user_preferences(user_name: str) -> list:
    """Get all preferences for a user."""
    return _user_preferences.get(user_name, [])



