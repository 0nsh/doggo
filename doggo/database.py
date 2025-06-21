"""ChromaDB operations and collections for Doggo."""

import chromadb
from pathlib import Path
from typing import Optional, List, Dict, Any
from chromadb.config import Settings


def get_chroma_db_dir() -> Path:
    """Get the ChromaDB persistence directory path."""
    return Path.home() / ".doggo" / "chroma_db"


def create_chroma_db_dir() -> None:
    """Create the ChromaDB persistence directory if it doesn't exist."""
    chroma_dir = get_chroma_db_dir()
    chroma_dir.mkdir(parents=True, exist_ok=True)


def initialize_chroma_db() -> None:
    """Initialize ChromaDB directory structure."""
    create_chroma_db_dir()


def get_chroma_client():
    """Get ChromaDB client instance."""
    chroma_dir = get_chroma_db_dir()
    return chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(anonymized_telemetry=False)
    )


def get_images_collection():
    """Get or create the images collection."""
    client = get_chroma_client()
    
    try:
        collection = client.get_collection("images")
    except:
        collection = client.create_collection(
            name="images",
            metadata={"description": "Semantic search for images"}
        )
    
    return collection


def add_image_to_index(
    file_hash: str,
    embedding: List[float],
    description: str,
    metadata: Dict[str, Any]
) -> None:
    """Add an image to the ChromaDB index."""
    collection = get_images_collection()
    
    # Add indexed_time to metadata
    import time
    metadata["indexed_time"] = int(time.time())
    
    collection.add(
        embeddings=[embedding],
        documents=[description],
        metadatas=[metadata],
        ids=[file_hash]
    )


def get_indexed_files() -> List[str]:
    """Get list of file hashes that are already indexed."""
    collection = get_images_collection()
    results = collection.get(include=[])
    return results["ids"]


def get_index_stats() -> Dict[str, Any]:
    """Get statistics about the indexed images."""
    collection = get_images_collection()
    count = collection.count()
    
    return {
        "total_images": count,
        "collection_name": "images"
    } 