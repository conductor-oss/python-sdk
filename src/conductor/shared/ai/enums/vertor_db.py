from enum import Enum


class VectorDB(str, Enum):
    PINECONE_DB = ("pineconedb",)
    WEAVIATE_DB = "weaviatedb"
