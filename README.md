# Universal Text-to-JSON Converter

A powerful, unified pipeline for converting **any** unstructured text to JSON following **any** JSON schema. Built with [Instructor](https://github.com/jxnl/instructor) and OpenAI GPT models.

## Features

- 🎯 **Universal**: Works with any text format and any JSON schema
- 📄 **PDF Support**: Automatic text extraction from PDF files
- 🔄 **Single Pipeline**: One simple API for all conversions
- ✅ **Schema Validation**: Automatic validation and retries
- 🚀 **Production Ready**: Built on Instructor (3M+ downloads/month)
- 📊 **Large Scale Support**: Handles 50k+ text inputs and 100k+ schemas
- 🎨 **Beautiful CLI**: Rich terminal interface with progress indicators

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd text-to-json-converter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Or set it as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Command Line Interface

Basic usage:
```bash
python main.py input.txt schema.json
```

With PDF files:
```bash
python main.py paper.pdf citation_schema.json
python main.py resume.pdf resume_schema.json -o resume.json
```

With options:
```bash
python main.py resume.txt resume_schema.json -o resume.json --model gpt-4o
```

### Python API

```python
from src.converter import UniversalTextToJSONConverter

# Initialize converter
converter = UniversalTextToJSONConverter()

# Convert text to JSON
result = converter.convert(
    text="John is 25 years old and lives in New York",
    schema="person_schema.json"
)

print(result)
# {"name": "John", "age": 25, "city": "New York"}
```

## CLI Commands

### Convert
Convert unstructured text to JSON:
```bash
python main.py convert input.txt schema.json [OPTIONS]

Options:
  -o, --output PATH      Output file path (defaults to input.json)
  -k, --api-key TEXT     OpenAI API key
  -m, --model TEXT       Model to use (defaults to gpt-4o)
  --pretty/--compact     Pretty print JSON output
  --show/--no-show       Display output in terminal
```

### Validate
Validate a JSON schema file:
```bash
python main.py validate schema.json
```

### Test
Run tests with sample data:
```bash
python main.py test          # Test all cases
python main.py test 1        # Test specific case
python main.py test --samples /path/to/samples
```

## Test Cases

The converter handles three challenging test cases:

1. **BibTeX → Citation Schema** (62KB schema, 1883 lines)
   - Structured text to complex nested schema
   - Handles special characters and author lists

2. **Natural Language → GitHub Actions** (30KB schema, 696 lines)
   - Unstructured description to workflow definition
   - Understands implicit relationships

3. **Resume → JSON Schema** (15KB schema, 501 lines)
   - Free-form text to structured resume
   - Flexible parsing of various formats

## How It Works

1. **Input Processing**: Automatically detects and extracts text from PDFs or reads text files
2. **Schema Analysis**: Dynamically converts JSON schemas to Pydantic models
3. **Intelligent Extraction**: Uses GPT-4o with optimized prompts
4. **Validation & Retries**: Automatic validation with up to 3 retries
5. **Universal Pipeline**: Same code path for all conversions

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Input     │────▶│    Schema    │────▶│  Universal  │────▶│   Output     │
│   Text      │     │   Analyzer   │     │  Converter  │     │    JSON      │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
```

## Key Features

### Dynamic Schema Handling
- Converts any JSON schema to Pydantic models on-the-fly
- Supports nested objects (7+ levels deep)
- Handles complex types (oneOf, anyOf, allOf)
- Manages large enums (1000+ values)

### Intelligent Prompting
- Optimized prompts for different schema sizes
- Schema summarization for large contexts
- Clear extraction rules for accuracy

### Robust Error Handling
- Automatic retries on validation failure
- Fallback strategies for large schemas
- Detailed error messages

## Configuration

Environment variables (in `.env`):
```bash
OPENAI_API_KEY=your-api-key-here
DEFAULT_MODEL=gpt-4o
MAX_RETRIES=3
TEMPERATURE=0
```

## Performance

- **Token Limits**: Handles 50k+ input tokens
- **Schema Size**: Supports 100k+ token schemas
- **Accuracy**: Prioritized over speed
- **Caching**: Reuses parsed schemas for efficiency

## Development

Run tests:
```bash
python main.py test
```

Format code:
```bash
black src/
ruff check src/
```

## Architecture

The converter follows a simple, unified architecture:

1. **Load Schema** → Parse JSON schema file
2. **Create Model** → Generate Pydantic model dynamically
3. **Extract Data** → Use Instructor + GPT-4o
4. **Validate** → Automatic validation and retries
5. **Output JSON** → Return structured data

## Trade-offs

- **Accuracy over Speed**: Uses larger models for better results
- **Flexibility over Simplicity**: Handles any schema at the cost of complexity
- **Robustness over Efficiency**: Multiple retries ensure reliability

## Future Improvements

- [ ] Parallel processing for multiple files
- [ ] Streaming support for very large inputs
- [ ] Fine-tuned models for specific domains
- [ ] Web interface for non-technical users
- [ ] Schema learning from examples

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built with:
- [Instructor](https://github.com/jxnl/instructor) - Structured outputs for LLMs
- [OpenAI](https://openai.com) - GPT-4o language model
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
