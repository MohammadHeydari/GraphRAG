import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph

# load env
load_dotenv()

graph = Neo4jGraph(
    url=os.environ["NEO4J_URI"],
    username=os.environ["NEO4J_USERNAME"],
    password=os.environ["NEO4J_PASSWORD"],
)

result = graph.query("RETURN 'Hello Neo4j' AS message")
print(result)