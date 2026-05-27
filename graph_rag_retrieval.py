from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("intfloat/multilingual-e5-base")

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("your-neo4j-username", "your-neo4j-password")
)

# Utils
def cosine(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def embed(text):
    return model.encode(text).tolist()

# 1. Vector retrieval
def retrieve_topk(query, k=5):
    qv = embed(query)

    with driver.session() as session:
        res = session.run("""
        MATCH (a:Article)
        RETURN a.title AS title,
               a.abstract AS abstract,
               a.embedding AS embedding
        """)

        scores = []

        for r in res:
            if not r["embedding"]:
                continue
            score = cosine(qv, r["embedding"])
            scores.append((r["title"], score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k], qv

# 2. Weighted Graph Expansion
def expand_graph(titles):
    with driver.session() as session:
        res = session.run("""
        MATCH (a:Article)
        WHERE a.title IN $titles

        OPTIONAL MATCH (a)<-[:PUBLISHED]-(r:Researcher)
        OPTIONAL MATCH (a)-[:IN_TOPIC]->(t:Topic)
        OPTIONAL MATCH (a)-[:IN_SUBTOPIC]->(s:Subtopic)

        OPTIONAL MATCH (a)-[:IN_TOPIC]->(:Topic)<-[:IN_TOPIC]-(a2:Article)
        OPTIONAL MATCH (a)-[:IN_SUBTOPIC]->(:Subtopic)<-[:IN_SUBTOPIC]-(a3:Article)

        RETURN a.title AS article,
               collect(DISTINCT r.name) AS authors,
               collect(DISTINCT t.name) AS topics,
               collect(DISTINCT s.name) AS subtopics,
               collect(DISTINCT a2.title) AS topic_links,
               collect(DISTINCT a3.title) AS subtopic_links
        """, {"titles": titles})

        return list(res)

# 3. Scoring / Pruning
def score_node(base_titles, row):
    score = 0

    # overlap boost
    score += len(set(row["topics"])) * 0.4
    score += len(set(row["subtopics"])) * 0.3

    # graph richness
    score += len(set(row["topic_links"])) * 0.2
    score += len(set(row["subtopic_links"])) * 0.2

    # small author signal
    score += len(set(row["authors"])) * 0.1

    return score

# 4. Build final context
def build_context(rows, top_n=3):
    scored = []

    for r in rows:
        s = score_node(None, r)
        scored.append((r, s))

    scored.sort(key=lambda x: x[1], reverse=True)

    final = scored[:top_n]

    context = []
    for r, s in final:
        context.append({
            "article": r["article"],
            "score": float(s),
            "authors": list(set(r["authors"])),
            "topics": list(set(r["topics"])),
            "subtopics": list(set(r["subtopics"])),
            "related_topic_articles": list(set(r["topic_links"])),
            "related_subtopic_articles": list(set(r["subtopic_links"]))
        })

    return context

# MAIN
def graph_rag(query):
    print("\nQuery:", query)

    topk, qv = retrieve_topk(query)

    print("\nTop-K:")
    for t, s in topk:
        print("-", t, s)

    titles = [t[0] for t in topk]

    expanded = expand_graph(titles)

    context = build_context(expanded)

    print("\nFINAL GRAPHRAG CONTEXT (PRUNED):")

    for c in context:
        print("\n", c["article"], " | score:", c["score"])
        print("", c["authors"])
        print("", c["topics"])
        print("topic links:", len(c["related_topic_articles"]))
        print("subtopic links:", len(c["related_subtopic_articles"]))

# TEST
if __name__ == "__main__":
    graph_rag("AI safety and ethics")