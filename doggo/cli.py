"""Main CLI entry point for Doggo."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

from doggo.config import initialize_doggo
from doggo.database import initialize_chroma_db
from doggo.indexer import index_directory
from doggo.database import get_index_stats
from doggo.searcher import search_similar_images, get_top_result_preview
from doggo.utils import open_in_native_previewer


console = Console()


@click.group()
def main():
    """Doggo - Semantic file search using AI."""
    pass


@main.command()
def init():
    """Initialize Doggo configuration and directories."""
    try:
        initialize_doggo()
        initialize_chroma_db()
        
        success_message = Panel(
            "[green]✅ Doggo initialized successfully![/green]\n\n"
            "Configuration directory: ~/.doggo/\n"
            "ChromaDB directory: ~/.doggo/chroma_db/\n\n"
            "Next steps:\n"
            "• Set your OpenAI API key: doggo config set-key <your-key>\n"
            "• Start indexing files: doggo index <path>",
            title="[bold blue]Doggo Initialized[/bold blue]",
            border_style="green"
        )
        console.print(success_message)
        
    except Exception as e:
        error_message = Panel(
            f"[red]❌ Failed to initialize Doggo: {str(e)}[/red]",
            title="[bold red]Initialization Error[/bold red]",
            border_style="red"
        )
        console.print(error_message)
        raise click.Abort()


@main.group()
def config():
    """Manage Doggo configuration."""
    pass


@config.command("set-key")
@click.argument("key")
def set_key(key):
    """Set the OpenAI API key for Doggo."""
    from .config import set_api_key, validate_api_key
    try:
        set_api_key(key)
        console.print(Panel(
            "[green]✅ OpenAI API key set successfully![/green]",
            title="[bold blue]Config Updated[/bold blue]",
            border_style="green"
        ))
    except ValueError as e:
        console.print(Panel(
            f"[red]❌ {str(e)}[/red]",
            title="[bold red]Invalid API Key[/bold red]",
            border_style="red"
        ))
        raise click.Abort()
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Failed to set API key: {str(e)}[/red]",
            title="[bold red]Config Error[/bold red]",
            border_style="red"
        ))
        raise click.Abort()


@config.command("show")
def show():
    """Show current Doggo configuration."""
    from .config import get_config_summary
    try:
        summary = get_config_summary()
        table = Table(title="Doggo Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Key", style="dim")
        table.add_column("Value")
        for k, v in summary.items():
            table.add_row(str(k), str(v))
        console.print(table)
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Failed to load configuration: {str(e)}[/red]",
            title="[bold red]Config Error[/bold red]",
            border_style="red"
        ))
        raise click.Abort()


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Show what would be indexed without actually indexing")
def index(path, dry_run):
    """Index images in the specified directory."""
    try:
        if dry_run:
            console.print(f"🔍 [yellow]Dry run:[/yellow] Would index images in {path}")
        else:
            console.print(f"⚡ [blue]Indexing[/blue] {path} recursively...")
        
        # Perform indexing
        result = index_directory(path, dry_run=dry_run)
        
        # Display results
        if dry_run:
            console.print(Panel(
                f"[yellow]📊 Dry Run Results[/yellow]\n\n"
                f"📁 Total images found: {result['total_found']}\n"
                f"⏭️  Would skip (already indexed): {result['skipped']}\n"
                f"🔄 Would process: {result['would_process']}\n",
                title="[bold blue]Index Preview[/bold blue]",
                border_style="yellow"
            ))
        else:
            # Get index stats
            stats = get_index_stats()
            
            console.print(Panel(
                f"[green]✅ Indexing completed![/green]\n\n"
                f"📁 Total images found: {result['total_found']}\n"
                f"✅ Processed: {result['processed']}\n"
                f"⏭️  Skipped (already indexed): {result['skipped']}\n"
                f"❌ Errors: {result['errors']}\n"
                f"📊 Total indexed images: {stats['total_images']}\n",
                title="[bold blue]Index Results[/bold blue]",
                border_style="green"
            ))
            
            if result['errors'] > 0:
                console.print(Panel(
                    f"[red]❌ Errors encountered:[/red]\n\n" + 
                    "\n".join(result['errors_list'][:5]) + 
                    (f"\n... and {len(result['errors_list']) - 5} more" if len(result['errors_list']) > 5 else ""),
                    title="[bold red]Errors[/bold red]",
                    border_style="red"
                ))
        
    except Exception as e:
        error_message = Panel(
            f"[red]❌ Failed to index directory: {str(e)}[/red]",
            title="[bold red]Indexing Error[/bold red]",
            border_style="red"
        )
        console.print(error_message)
        raise click.Abort()


@main.command()
@click.argument("query")
@click.option("--limit", default=5, help="Maximum number of results to return (default: 5)")
@click.option("--preview", is_flag=True, help="Show detailed preview of top result")
@click.option("--no-open", is_flag=True, help="Don't automatically open the top result")
def search(query, limit, preview, no_open):
    """Search for images using natural language queries."""
    try:
        console.print(f"🔍 [blue]Searching[/blue] for: '{query}'")
        
        # Perform search
        results = search_similar_images(query, limit=limit)
        
        if not results:
            console.print(Panel(
                "[yellow]No results found for your query.[/yellow]\n\n"
                "Try:\n"
                "• Using different keywords\n"
                "• Checking if you have indexed any images\n"
                "• Running 'doggo index <path>' to index some images",
                title="[bold blue]No Results[/bold blue]",
                border_style="yellow"
            ))
            return
        
        # Show preview of top result if requested
        if preview and results:
            top_result = results[0]
            preview_text = get_top_result_preview(top_result)
            console.print(Panel(
                preview_text,
                title="[bold green]Top Result Preview[/bold green]",
                border_style="green"
            ))
            console.print()  # Add spacing
        
        # Display search results table
        table = Table(title=f"Search Results for '{query}'", show_header=True, header_style="bold magenta")
        table.add_column("Rank", style="dim", width=6)
        table.add_column("Similarity", style="dim", width=10)
        table.add_column("File", style="cyan")
        table.add_column("Path", style="dim")
        table.add_column("Description", style="white")
        
        for i, result in enumerate(results, 1):
            metadata = result['metadata']
            file_name = metadata.get('file_name', 'Unknown')
            file_path = metadata.get('file_path', 'Unknown')
            similarity = result['similarity_score']
            description = result['description'][:80] + "..." if len(result['description']) > 80 else result['description']
            
            table.add_row(
                str(i),
                f"{similarity:.1%}",
                file_name,
                file_path,
                description
            )
        
        console.print(table)
        
        # Show summary
        console.print(Panel(
            f"[green]Found {len(results)} results[/green]\n"
            f"Top similarity: {results[0]['similarity_score']:.1%}",
            title="[bold blue]Search Summary[/bold blue]",
            border_style="green"
        ))
        
        # Automatically open the top result if not disabled
        if results and not no_open:
            top_result_path = Path(results[0]['metadata']['file_path'])
            
            console.print(f"\n🖼️  [blue]Opening top result:[/blue] {top_result_path.name}")
            
            if open_in_native_previewer(top_result_path):
                console.print("[green]✅ Opened in native previewer[/green]")
            else:
                console.print("[yellow]⚠️  Could not open in native previewer[/yellow]")
        
    except ValueError as e:
        console.print(Panel(
            f"[red]❌ {str(e)}[/red]",
            title="[bold red]Search Error[/bold red]",
            border_style="red"
        ))
        raise click.Abort()
    except Exception as e:
        console.print(Panel(
            f"[red]❌ Failed to perform search: {str(e)}[/red]",
            title="[bold red]Search Error[/bold red]",
            border_style="red"
        ))
        raise click.Abort()


if __name__ == "__main__":
    main() 