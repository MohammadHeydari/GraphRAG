from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-base")

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "19931440")
)

query = "AI safety and ethics"
query_vec = model.encode(query).tolist()

with driver.session() as session:
    result = session.run("""
    CALL db.index.vector.queryNodes(
        'article_index',
        5,
        $embedding
    )
    YIELD node, score
    RETURN node.title AS title, score
    ORDER BY score DESC
    """, {"embedding": query_vec})

    for r in result:
        print(r["title"], r["score"])