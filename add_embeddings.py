from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("intfloat/multilingual-e5-base")

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "19931440")
)

def embed(text):
    return model.encode(text).tolist()

def add_embeddings(tx):
    result = tx.run("""
    MATCH (a:Article)
    RETURN elementId(a) AS id, a.title AS title, a.abstract AS abstract
    """)

    for r in result:
        title = r["title"] or ""
        abstract = r["abstract"] or ""

        text = title + " " + abstract
        vector = embed(text)

        tx.run("""
        MATCH (a)
        WHERE elementId(a) = $id
        SET a.embedding = $embedding
        """, {
            "id": r["id"],
            "embedding": vector
        })

with driver.session() as session:
    session.execute_write(add_embeddings)

print("Embeddings added successfully")