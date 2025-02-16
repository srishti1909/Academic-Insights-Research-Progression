from neo4j import GraphDatabase, basic_auth
from config.neo4j_config import NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DB_NAME, NEO4J_HOST, NEO4J_PORT

# Create a Neo4j driver instance
neo4j_driver = GraphDatabase.driver(f"bolt://{NEO4J_HOST}:{NEO4J_PORT}",
                                    auth=basic_auth(NEO4J_USERNAME, NEO4J_PASSWORD),
                                    database=NEO4J_DB_NAME)
