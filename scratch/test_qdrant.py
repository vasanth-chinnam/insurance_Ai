from qdrant_client import QdrantClient

print("Bases of QdrantClient:", QdrantClient.__bases__)
print("Methods of QdrantClient:", [m for m in dir(QdrantClient) if not m.startswith("_")])
