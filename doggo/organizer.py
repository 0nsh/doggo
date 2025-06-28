from pathlib import Path
from typing import List, Dict, Optional

def organize_images(location, rename=False, output=None, inplace=False):
    """
    Organizes images in the specified location into category folders based on indexed data.
    Optionally renames files using AI-generated filenames.
    """
    location = Path(location)
    if not location.exists() or not location.is_dir():
        raise ValueError(f"Location {location} does not exist or is not a directory.")

    if output and inplace:
        raise ValueError("--output and --inplace are mutually exclusive.")

    if inplace:
        output_dir = location
    elif output:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = location / "organized"
        output_dir.mkdir(parents=True, exist_ok=True)

    # Load indexed data for this location
    indexed_data = load_indexed_data(location)
    if not indexed_data:
        from rich.panel import Panel
        from rich.console import Console
        console = Console()
        console.print(Panel(f"[yellow]No indexed images found in {location}.[/yellow]", title="[bold yellow]No Indexed Images[/bold yellow]", border_style="yellow"))
        return

    # Generate categories
    category_map = generate_categories(indexed_data)

    # Move and optionally rename files
    move_and_rename_files(category_map, output_dir, rename, indexed_data)

    from rich.panel import Panel
    from rich.console import Console
    console = Console()
    console.print(Panel(f"[green]✅ Organized {sum(len(v) for v in category_map.values())} images into {len(category_map)} categories.[/green]", title="[bold blue]Organize Complete[/bold blue]", border_style="green"))


def load_indexed_data(location):
    """
    Loads indexed data (captions, tags, etc.) for images in the given location.
    Returns a list of dicts with image paths and associated metadata.
    """
    from doggo.database import get_images_collection
    from doggo.utils import is_image_file
    location = Path(location)
    collection = get_images_collection()
    # Get all indexed images and their metadata
    results = collection.get(include=["documents", "metadatas"])
    if results is None:
        return []

    indexed = []
    for i in range(len(results["ids"])):
        metadata = results["metadatas"][i] if results["metadatas"] else None
        file_path = metadata.get("file_path", "") if metadata else None
        if not file_path or not isinstance(file_path, (str, Path)):
            continue
        file_path = Path(file_path)
        if is_image_file(file_path) and location in file_path.parents:
            indexed.append({
                "file_path": file_path,
                "description": results["documents"][i] if results["documents"] else None,
                "metadata": metadata
            })
    return indexed


def generate_categories(indexed_data):
    """
    Groups images by their AI-driven 'category' field in metadata.
    """
    from collections import defaultdict
    category_map = defaultdict(list)
    for item in indexed_data:
        category = None
        if isinstance(item, dict):
            meta = item.get("metadata", {})
            category = meta.get("category")
        if not category or not isinstance(category, str) or not category.strip():
            category = "uncategorized"
        category = category.strip().replace(" ", "_").lower()
        category_map[category].append(item["file_path"] if isinstance(item, dict) and "file_path" in item else None)
    # Remove any None entries
    return {cat: [fp for fp in files if fp is not None] for cat, files in category_map.items()}


def move_and_rename_files(category_map, output_dir, rename, indexed_data=None):
    """
    Moves (and optionally renames) images into category folders in the output directory.
    """
    from doggo.utils import extract_file_metadata
    
    # Create lookup for AI-generated filenames from indexed data
    filename_lookup = {}
    if indexed_data and rename:
        for item in indexed_data:
            if isinstance(item, dict) and "file_path" in item and "metadata" in item:
                file_path_str = str(item["file_path"])
                metadata = item["metadata"]
                if isinstance(metadata, dict) and "filename" in metadata:
                    filename_lookup[file_path_str] = metadata["filename"]
    
    for category, files in category_map.items():
        cat_dir = create_category_directory(output_dir, category)
        for file_path in files:
            if not file_path or not isinstance(file_path, (str, Path)):
                continue
            file_path = Path(file_path)
            if not file_path.exists() or not file_path.is_file():
                continue
            metadata = None
            if rename:
                try:
                    metadata = extract_file_metadata(file_path)
                    # Add AI-generated filename if available
                    file_path_str = str(file_path)
                    if file_path_str in filename_lookup:
                        metadata["filename"] = filename_lookup[file_path_str]
                except Exception:
                    metadata = {"file_name": file_path.name, "file_type": file_path.suffix.lstrip('.') or "jpg"}
            if not isinstance(metadata, dict):
                metadata = {"file_name": file_path.name, "file_type": file_path.suffix.lstrip('.') or "jpg"}
            dest_path = get_destination_path(cat_dir, file_path, rename, metadata)
            copy_file_to_category(file_path, dest_path)

def create_category_directory(output_dir, category):
    """
    Creates and returns the directory for a category.
    """
    cat_dir = output_dir / category.replace(" ", "_")
    cat_dir.mkdir(parents=True, exist_ok=True)
    return cat_dir

def get_destination_path(cat_dir, file_path, rename, metadata):
    """
    Determines the destination path for a file, handling renaming and duplicates.
    """
    from pathlib import Path
    if not isinstance(file_path, Path):
        file_path = Path(file_path)
    if not isinstance(metadata, dict):
        metadata = {"file_name": file_path.name, "file_type": file_path.suffix.lstrip('.') or "jpg"}
    if rename:
        new_name = generate_descriptive_filename(metadata)
        dest_path = cat_dir / new_name
    else:
        dest_path = cat_dir / file_path.name
    counter = 1
    orig_dest = dest_path
    while dest_path.exists():
        dest_path = cat_dir / f"{orig_dest.stem}_{counter}{orig_dest.suffix}"
        counter += 1
    return dest_path

def copy_file_to_category(file_path, dest_path):
    """
    Copies the file to the destination.
    """
    import shutil
    shutil.copy2(file_path, dest_path)


def generate_descriptive_filename(metadata):
    """
    Generates a descriptive filename using the AI-generated filename from metadata.
    """
    if isinstance(metadata, dict) and "filename" in metadata:
        filename = metadata["filename"]
        if isinstance(filename, str) and filename.strip():
            # Get file extension from metadata or use default
            ext = metadata.get("file_type", "jpg")
            if not isinstance(ext, str) or not ext.strip():
                ext = "jpg"
            return f"{filename.strip()}.{ext}"
    
    # Fallback to original filename
    if isinstance(metadata, dict) and "file_name" in metadata:
        return metadata["file_name"]
    
    return "image.jpg"
