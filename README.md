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

</p>
<hr>

Doggo is a CLI tool that uses AI to help you search for images using natural language queries. Instead of remembering exact filenames, just describe what you're looking for! 

## Features

- 🔍 **Semantic Search**: Find images by describing them in natural language
- 🎯 **Smart Results**: AI-powered similarity matching
- 💻 **CLI Interface**: Simple command-line interface
- 📊 **Rich Output**: Beautiful, informative search results

## Demo

TO BE ADDED


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


## How it works

- **AI-Powered Indexing**: Doggo scans directories for images, uses OpenAI's Vision API to generate detailed descriptions of each image, and converts these descriptions into vector embeddings using OpenAI's Embeddings API for semantic search capabilities.

- **Vector Database Storage**: The tool stores image metadata, AI-generated descriptions, and vector embeddings in a local ChromaDB database, enabling fast similarity-based retrieval without needing to re-process images on each search.

- **Natural Language Search**: Users can search for images using descriptive queries like "cute dog playing in the park" - the system converts the query to a vector embedding and finds the most semantically similar images using vector similarity search.

- **CLI Interface**: Provides a simple command-line interface with commands for initialization (doggo init), configuration (doggo config set-key), indexing (doggo index <path>), and searching (doggo search "query") with rich output formatting and progress tracking.


## Contributing

- Contributions are welcome! Please feel free to submit a pull request.
- See open issues for ideas.

## License

MIT License - see the [LICENSE](LICENSE) file for details.