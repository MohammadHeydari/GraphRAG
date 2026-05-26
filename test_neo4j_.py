from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "add_your_neo4j_password_here") # add_your_neo4j_password_here
)

with driver.session() as session:
    result = session.run("RETURN 1 AS num")
    print(result.single()["num"])