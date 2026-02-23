from neo4j import GraphDatabase
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Neo4jClient:
    """
    Singleton wrapper for Neo4j connections.
    Fixed: Proper result handling to avoid consumption errors.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_username, settings.neo4j_password)
            )
        return cls._instance

    def execute_query(self, query: str, params: dict = None):
        """Execute a query and return all results properly."""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                # Fetch ALL records before session closes
                records = list(result)
                return records
        except Exception as e:
            logger.error(f"Neo4j Error: {e}")
            raise

    def execute_write(self, query: str, params: dict = None):
        """Execute a write transaction with proper error handling."""
        try:
            with self.driver.session() as session:
                result = session.run(query, params or {})
                # Consume result to ensure transaction completes
                result.consume()
                return True
        except Exception as e:
            logger.error(f"Neo4j Write Error: {e}")
            raise

    def close(self):
        if self._instance and self._instance.driver:
            self._instance.driver.close()