"""
Command-line interface for the Universal Text-to-JSON Converter.

Provides a user-friendly CLI for converting unstructured text to JSON
following any schema.
"""

import typer
from pathlib import Path
import json
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from typing import Optional
import os
from dotenv import load_dotenv

from converter import UniversalTextToJSONConverter
from pdf_handler import PDFHandler

# Load environment variables
load_dotenv()

app = typer.Typer(
    name="text2json",
    help="Convert unstructured text to JSON following any schema",
    add_completion=False,
)
console = Console()


@app.command()
def convert(
    input_file: Path = typer.Argument(
        ...,
        help="Path to input text file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    schema_file: Path = typer.Argument(
        ...,
        help="Path to JSON schema file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (defaults to input_file.json)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="OpenAI API key (defaults to OPENAI_API_KEY env var)",
        envvar="OPENAI_API_KEY",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Model to use (defaults to gpt-4.1)",
    ),
    pretty: bool = typer.Option(
        True,
        "--pretty/--compact",
        help="Pretty print JSON output",
    ),
    show_output: bool = typer.Option(
        True,
        "--show/--no-show",
        help="Display output in terminal",
    ),
):
    """
    Convert unstructured text to JSON following a schema.
    
    Examples:
        text2json input.txt schema.json
        text2json resume.txt resume_schema.json -o resume.json
        text2json --model gpt-4-turbo input.txt schema.json
    """
    # Display header
    console.print(
        Panel.fit(
            "[bold blue]Universal Text-to-JSON Converter[/bold blue]\n"
            "[dim]Converting unstructured text to structured JSON[/dim]",
            border_style="blue",
        )
    )
    
    # Display input info
    table = Table(show_header=False, box=None)
    table.add_row("[bold]Input file:[/bold]", str(input_file))
    table.add_row("[bold]Schema file:[/bold]", str(schema_file))
    table.add_row("[bold]Model:[/bold]", model or "gpt-4.1 (default)")
    console.print(table)
    console.print()
    
    try:
        # Read input text
        console.print("[dim]Reading input file...[/dim]")
        
        # Check if input is PDF
        if PDFHandler.is_pdf(input_file):
            console.print("[dim]Detected PDF file, extracting text...[/dim]")
            text = PDFHandler.extract_text(input_file)
            
            # Apply preprocessing based on file name hints
            if "resume" in str(input_file).lower() or "cv" in str(input_file).lower():
                console.print("[dim]Applying resume preprocessing...[/dim]")
                text = PDFHandler.preprocess_resume(text)
            elif "paper" in str(input_file).lower() or "article" in str(input_file).lower():
                console.print("[dim]Applying academic paper preprocessing...[/dim]")
                text = PDFHandler.preprocess_academic_paper(text)
        else:
            text = input_file.read_text(encoding="utf-8")
            
        console.print(f"[green]✓[/green] Read {len(text):,} characters")
        
        # Initialize converter
        converter = UniversalTextToJSONConverter(api_key=api_key, model=model)
        
        # Convert
        console.print("\n[bold]Converting...[/bold]")
        result = converter.convert(text, schema_file)
        
        # Determine output file
        if output_file is None:
            output_file = input_file.with_suffix(".json")
        
        # Save output
        console.print(f"\n[dim]Saving to {output_file}...[/dim]")
        with open(output_file, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                json.dump(result, f, ensure_ascii=False)
        
        console.print(f"[green]✓[/green] Output saved to [bold]{output_file}[/bold]")
        
        # Display output if requested
        if show_output:
            console.print("\n[bold]Output:[/bold]")
            json_str = json.dumps(result, indent=2, ensure_ascii=False)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            console.print(syntax)
        
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in schema file: {e}")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def validate(
    schema_file: Path = typer.Argument(
        ...,
        help="Path to JSON schema file to validate",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Validate a JSON schema file.
    
    Example:
        text2json validate schema.json
    """
    console.print(
        Panel.fit(
            "[bold blue]Schema Validator[/bold blue]",
            border_style="blue",
        )
    )
    
    try:
        # Load and parse schema
        with open(schema_file) as f:
            schema = json.load(f)
        
        # Basic validation
        if "properties" not in schema:
            console.print("[yellow]Warning:[/yellow] Schema has no 'properties' field")
        
        # Display schema info
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        console.print(f"\n[bold]Schema: {schema.get('title', 'Untitled')}[/bold]")
        console.print(f"Description: {schema.get('description', 'No description')}")
        console.print(f"Total fields: {len(properties)}")
        console.print(f"Required fields: {len(required)}")
        
        # Display fields table
        if properties:
            console.print("\n[bold]Fields:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Field", style="cyan", no_wrap=True)
            table.add_column("Type", style="green")
            table.add_column("Required", justify="center")
            table.add_column("Description")
            
            for name, prop in properties.items():
                field_type = prop.get("type", "unknown")
                is_required = "✓" if name in required else ""
                description = prop.get("description", "")[:50]
                if len(prop.get("description", "")) > 50:
                    description += "..."
                
                table.add_row(name, field_type, is_required, description)
            
            console.print(table)
        
        console.print("\n[green]✓[/green] Schema is valid!")
        
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def test(
    test_case: Optional[int] = typer.Argument(
        None,
        help="Test case number (1-3) or leave empty to test all",
        min=1,
        max=3,
    ),
    samples_dir: Path = typer.Option(
        Path("../samples"),
        "--samples",
        "-s",
        help="Path to samples directory",
    ),
):
    """
    Test the converter with sample test cases.
    
    Examples:
        text2json test          # Test all cases
        text2json test 1        # Test case 1 only
        text2json test --samples /path/to/samples
    """
    console.print(
        Panel.fit(
            "[bold blue]Test Runner[/bold blue]",
            border_style="blue",
        )
    )
    
    # Define test cases
    test_cases = {
        1: {
            "name": "BibTeX to Citation Schema",
            "input": "test case 1/NIPS-2017-attention-is-all-you-need-Bibtex.txt",
            "schema": "test case 1/paper citations_schema.json",
        },
        2: {
            "name": "GitHub Actions Natural Language",
            "input": "test case 2/github actions sample input.txt",
            "schema": "test case 2/github_actions_schema.json",
        },
        3: {
            "name": "Resume to JSON Schema",
            "input": None,  # Will need to create sample
            "schema": "test case 3/convert your resume to this schema.json",
        },
    }
    
    # Determine which tests to run
    if test_case:
        tests_to_run = [test_case]
    else:
        tests_to_run = [1, 2, 3]
    
    # Initialize converter
    try:
        converter = UniversalTextToJSONConverter()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("[dim]Set OPENAI_API_KEY environment variable or use --api-key[/dim]")
        raise typer.Exit(1)
    
    # Run tests
    results = []
    for test_num in tests_to_run:
        test_info = test_cases[test_num]
        console.print(f"\n[bold]Test Case {test_num}: {test_info['name']}[/bold]")
        
        # Handle test case 3 (no input provided)
        if test_info["input"] is None:
            console.print("[yellow]Skipping:[/yellow] No input file provided for test case 3")
            results.append(("Test 3", "Skipped", "No input"))
            continue
        
        # Build paths
        input_path = samples_dir / test_info["input"]
        schema_path = samples_dir / test_info["schema"]
        
        # Check files exist
        if not input_path.exists():
            console.print(f"[red]Error:[/red] Input file not found: {input_path}")
            results.append((f"Test {test_num}", "Failed", "Input not found"))
            continue
        
        if not schema_path.exists():
            console.print(f"[red]Error:[/red] Schema file not found: {schema_path}")
            results.append((f"Test {test_num}", "Failed", "Schema not found"))
            continue
        
        try:
            # Read input
            text = input_path.read_text(encoding="utf-8")
            console.print(f"Input size: {len(text):,} characters")
            
            # Convert
            result = converter.convert(text, schema_path)
            
            # Save output
            output_path = samples_dir / f"test_case_{test_num}_output.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✓[/green] Success! Output saved to {output_path}")
            results.append((f"Test {test_num}", "Passed", str(output_path)))
            
        except Exception as e:
            console.print(f"[red]✗[/red] Failed: {str(e)}")
            results.append((f"Test {test_num}", "Failed", str(e)[:50]))
    
    # Display summary
    console.print("\n[bold]Test Summary:[/bold]")
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Status", justify="center")
    summary_table.add_column("Details")
    
    for test, status, details in results:
        style = "green" if status == "Passed" else "red" if status == "Failed" else "yellow"
        summary_table.add_row(test, f"[{style}]{status}[/{style}]", details)
    
    console.print(summary_table)


if __name__ == "__main__":
    app() 