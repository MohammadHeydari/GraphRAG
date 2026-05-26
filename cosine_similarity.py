from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("intfloat/multilingual-e5-base")

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "19931440")
)

def cosine(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

query = "AI safety and ethics"
query_vec = model.encode(query).tolist()

with driver.session() as session:
    result = session.run("""
    MATCH (a:Article)
    RETURN a.title AS title, a.abstract AS abstract, a.embedding AS embedding
    """)

    scores = []

    for r in result:
        if r["embedding"] is None:
            continue

        text = (r["title"] or "") + " " + (r["abstract"] or "")
        score = cosine(query_vec, r["embedding"])

        scores.append((r["title"], score))

    scores.sort(key=lambda x: x[1], reverse=True)

    for title, score in scores[:5]:
        print(title, score)