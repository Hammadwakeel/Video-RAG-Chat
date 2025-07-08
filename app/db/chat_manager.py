# app/db/chat_manager.py
import uuid
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from ..config import settings

class ChatManagement:
    def __init__(self, connection_string, database_name, collection_name):
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name
        # map session_id to MongoDBChatMessageHistory instances
        self.chat_sessions = {}

    def _create_history(self, session_id: str) -> MongoDBChatMessageHistory:
        """
        Internal: create a new MongoDBChatMessageHistory for a session_id.
        """
        history = MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=self.connection_string,
            database_name=self.database_name,
            collection_name=self.collection_name
        )
        # store in memory
        self.chat_sessions[session_id] = history
        return history

    def get_chat_history(self, session_id: str) -> MongoDBChatMessageHistory | None:
        """
        Retrieve an existing chat history object from memory or database.
        Returns None if no history found.
        """
        # in-memory
        if session_id in self.chat_sessions:
            return self.chat_sessions[session_id]
        # instantiate from DB
        history = MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=self.connection_string,
            database_name=self.database_name,
            collection_name=self.collection_name
        )
        if history.messages:
            self.chat_sessions[session_id] = history
            return history
        return None

    def initialize_chat_history(self, session_id: str) -> MongoDBChatMessageHistory:
        """
        Ensure a chat history exists for the session_id. Return the history instance.
        """
        history = self.get_chat_history(session_id)
        if history:
            return history
        # no existing history, create new object (and DB entries)
        return self._create_history(session_id)

# create a global instance for use in routes
from ..config import settings
chat_manager = ChatManagement(
    settings.CONNECTION_STRING,
    settings.DATABASE_NAME,
    settings.COLLECTION_NAME
)
