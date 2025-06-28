<p align="center">
  <img src="./docs/doggo.png" width="400" height="200" style="border-radius: 10px;" alt="Doggo">

</p>
<p align="center">
    <em>Doggo 🐕, your loyal digital companion who finds files the way you think about them.</em>
</p>
<p align="center">
<a href="https://github.com/0nsh/doggo/actions/workflows/test.yaml" target="_blank">
    <img src="https://github.com/0nsh/doggo/actions/workflows/test.yaml/badge.svg" alt="Test">
</a>

<a href="https://pypi.org/project/doggo" target="_blank">
    <img src="https://img.shields.io/pypi/v/doggo?color=%2334D058&label=pypi%20package" alt="Package version">
</a>

</p>
<hr>

Doggo is a CLI tool that uses AI to help you search for and organize images using natural language queries. Instead of remembering exact filenames, just describe what you're looking for! 

## Features

- 🔍 **Semantic Search**: Find images by describing them in natural language
- 🗂️ **AI-Powered Organization**: Automatically organize images into intelligent categories
- ✏️ **Smart Renaming**: Generate descriptive filenames based on image content
- 🎯 **Smart Results**: AI-powered similarity matching
- 💻 **CLI Interface**: Simple command-line interface
- 📊 **Rich Output**: Beautiful, informative search results

## Demo

https://github.com/user-attachments/assets/568d7f3d-9ff6-4adb-89db-71455a174c46


## Usage

```bash
pip install doggo
```

## Quick Start

1. **Initialize Doggo:**
   ```bash
   doggo init
   ```

2. **Set your OpenAI API key:**
   ```bash
   doggo config set-key <your-openai-api-key>
   ```

3. **Index your images:**
   ```bash
   doggo index /path/to/your/images
   ```

4. **Search naturally:**
   ```bash
   doggo search "a cute dog playing in the park"
   doggo search "sunset over mountains"
   doggo search "people having dinner"
   ```
   
   By default, Doggo shows the top 5 results and automatically opens the best match in your system's previewer. Use `--no-open` to disable auto-opening or `--limit` to change the number of results.

5. **Organize your images:**
   ```bash
   # Organize images into AI-generated category folders
   doggo organize /path/to/your/images
   
   # Organize with descriptive filenames
   doggo organize /path/to/your/images --rename
   
   # Organize to a custom output directory
   doggo organize /path/to/your/images --rename --output /path/to/organized
   
   # Organize in place (within the same directory)
   doggo organize /path/to/your/images --inplace
   ```

## Organizing Images

Doggo can intelligently organize your images using AI-generated categories and descriptive filenames:

### **AI-Generated Categories**
During indexing, Doggo analyzes each image and assigns it to a category (e.g., "flower", "dog", "landscape", "food"). When you run the organize command, images are automatically grouped into folders based on these categories.

### **Smart Renaming**
With the `--rename` flag, Doggo generates descriptive filenames based on the image content. Instead of generic names like "IMG_001.jpg", you get meaningful names like "red_rose_garden.jpg" or "golden_retriever_park.jpg".

### **Organization Options**
- **Default**: Creates an "organized" folder in the source directory
- **Custom output**: Use `--output` to specify a different destination
- **In-place**: Use `--inplace` to organize within the original directory
- **Combined**: Use `--rename` with any output option for descriptive filenames

### **Example Organization**
```
Before:
📁 photos/
  ├── IMG_001.jpg (a red rose)
  ├── DSC_123.jpg (a dog in park)
  └── photo.jpg (sunset)

After:
📁 organized/
  ├── 📁 flower/
  │   └── red_rose_garden.jpg
  ├── 📁 dog/
  │   └── golden_retriever_park.jpg
  └── 📁 landscape/
      └── sunset_beach_view.jpg
```

## How it works

- **AI-Powered Indexing**: Doggo scans directories for images, uses OpenAI's Vision API to generate detailed descriptions and categories of each image, and converts these descriptions into vector embeddings using OpenAI's Embeddings API for semantic search capabilities.

- **Vector Database Storage**: The tool stores image metadata, AI-generated descriptions, categories, and vector embeddings in a local ChromaDB database, enabling fast similarity-based retrieval and intelligent organization without needing to re-process images on each search.

- **Natural Language Search**: Users can search for images using descriptive queries like "cute dog playing in the park" - the system converts the query to a vector embedding and finds the most semantically similar images using vector similarity search.

- **Intelligent Organization**: Using the AI-generated categories and descriptions, Doggo can automatically organize images into meaningful folders and generate descriptive filenames, making it easy to find and manage large collections of images.

- **CLI Interface**: Provides a simple command-line interface with commands for initialization (doggo init), configuration (doggo config set-key), indexing (doggo index <path>), searching (doggo search "query"), and organizing (doggo organize <path>) with rich output formatting and progress tracking.


## Contributing

- Contributions are welcome! Please feel free to submit a pull request.
- See open issues for ideas.

## License

MIT License - see the [LICENSE](LICENSE) file for details.