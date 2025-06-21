"""Image indexing and AI processing for Doggo."""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import openai

from doggo.utils import scan_image_files, extract_file_metadata, validate_image_file
from doggo.database import add_image_to_index, get_indexed_files
from doggo.config import load_config, add_indexed_path, update_last_reindex


def generate_image_description(image_path: Path) -> str:
    """Generate AI description for an image using OpenAI Vision API."""
    config = load_config()
    api_key = config.get("openai_api_key")
    
    if not api_key:
        raise ValueError("OpenAI API key not configured. Run 'doggo config set-key <your-key>'")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Load and prepare image
    with Image.open(image_path) as img:
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if too large (OpenAI has size limits)
        max_size = 1024
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save to bytes for API
        import io
        import base64
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        # Encode as base64
        base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
    
    # Generate description
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in detail for search purposes. Focus on visual elements, objects, colors, composition, and any text or symbols visible. Be specific and descriptive."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=150
    )
    
    return response.choices[0].message.content.strip() if response.choices[0].message.content else ""


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI Embeddings API."""
    config = load_config()
    api_key = config.get("openai_api_key")
    
    if not api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = openai.OpenAI(api_key=api_key)
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    
    return response.data[0].embedding


def process_single_image(image_path: Path) -> Dict[str, Any]:
    """Process a single image for indexing."""
    # Validate image
    if not validate_image_file(image_path):
        raise ValueError(f"Invalid or corrupted image: {image_path}")
    
    # Extract metadata
    metadata = extract_file_metadata(image_path)
    
    # Generate AI description
    description = generate_image_description(image_path)
    
    # Create searchable text (description + filename)
    searchable_text = f"{description} {image_path.name}"
    
    # Generate embedding
    embedding = generate_embedding(searchable_text)
    
    return {
        "file_hash": metadata["file_hash"],
        "embedding": embedding,
        "description": description,
        "metadata": metadata
    }


def index_directory(directory: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Index all images in a directory."""
    # Scan for image files
    image_files = scan_image_files(directory)
    
    if not image_files:
        return {
            "total_found": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "errors_list": []
        }
    
    # Get already indexed files
    indexed_files = set(get_indexed_files())
    
    # Filter out already indexed files
    new_files = [f for f in image_files if extract_file_metadata(f)["file_hash"] not in indexed_files]
    
    if dry_run:
        return {
            "total_found": len(image_files),
            "processed": 0,
            "skipped": len(image_files) - len(new_files),
            "errors": 0,
            "errors_list": [],
            "would_process": len(new_files)
        }
    
    # Process new files
    processed = 0
    errors = 0
    errors_list = []
    
    for image_path in new_files:
        try:
            result = process_single_image(image_path)
            add_image_to_index(
                result["file_hash"],
                result["embedding"],
                result["description"],
                result["metadata"]
            )
            processed += 1
            
        except Exception as e:
            errors += 1
            errors_list.append(f"{image_path}: {str(e)}")
    
    # Update configuration if indexing was successful
    if processed > 0:
        add_indexed_path(directory)
        update_last_reindex()
    
    return {
        "total_found": len(image_files),
        "processed": processed,
        "skipped": len(image_files) - len(new_files),
        "errors": errors,
        "errors_list": errors_list
    } 