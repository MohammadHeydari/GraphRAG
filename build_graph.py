import pandas as pd
from neo4j import GraphDatabase

# load csv
df = pd.read_csv("dataset/data.csv", sep=";")

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("your-neo4j-username", "your-neo4j-password")
)

def insert_row(tx, row):
    tx.run("""
    MERGE (a:Article {title: $title})
    SET a.abstract = $abstract,
        a.publication_date = date($date)

    MERGE (t:Topic {name: $topic})
    MERGE (a)-[:IN_TOPIC]->(t)

    MERGE (s:Subtopic {name: $subtopic})
    MERGE (a)-[:IN_SUBTOPIC]->(s)

    WITH a
    UNWIND split($authors, ',') AS author
    MERGE (r:Researcher {name: trim(author)})
    MERGE (r)-[:PUBLISHED]->(a)
    """, {
        "title": row["Title"],
        "abstract": row["Abstract"],
        "topic": row["Topic"],
        "subtopic": row["Subtopic"],
        "authors": row["Authors"],
        "date": row["Publication_Date"]
    })

with driver.session() as session:
    for _, row in df.iterrows():
        session.execute_write(insert_row, row)

print("Graph built successfully!")