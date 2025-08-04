"""
Universal Text-to-JSON Converter

This module provides a unified pipeline for converting any unstructured text
to JSON following any schema, using Instructor and OpenAI GPT models.
"""

import instructor
from openai import OpenAI
from pydantic import BaseModel, create_model, Field, ValidationError
from typing import Dict, Any, Type, Union, Optional, List, Literal
import json
import hashlib
import os
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class UniversalTextToJSONConverter:
    """
    Convert any unstructured text to JSON following any schema.
    No special cases, no complex logic - just one simple pipeline.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the converter with OpenAI client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (defaults to gpt-4.1)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY or pass api_key parameter.")
        
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4.1")
        self.client = instructor.from_openai(
            OpenAI(api_key=self.api_key),
            mode=instructor.Mode.TOOLS
        )
        self.model_cache = {}
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.temperature = float(os.getenv("TEMPERATURE", "0"))
    
    def convert(self, 
                text: str, 
                schema: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert unstructured text to JSON following the provided schema.
        
        Args:
            text: Any unstructured text (resume, bibtex, description, etc.)
            schema: JSON schema as file path, Path object, or dict
            
        Returns:
            Dictionary following the provided schema
            
        Raises:
            ValidationError: If the extraction fails validation
            FileNotFoundError: If schema file not found
            JSONDecodeError: If schema file is invalid JSON
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Load schema
            task = progress.add_task("Loading schema...", total=None)
            schema_dict = self._load_schema(schema)
            progress.update(task, completed=True)
            
            # Create Pydantic model
            task = progress.add_task("Creating model...", total=None)
            model = self._get_pydantic_model(schema_dict)
            progress.update(task, completed=True)
            
            # Extract using Instructor
            task = progress.add_task("Extracting information...", total=None)
            try:
                result = self._extract_with_retries(text, model, schema_dict)
                progress.update(task, completed=True)
                
                console.print("[green]✓[/green] Extraction successful!")
                return result.model_dump()
                
            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]✗[/red] Extraction failed: {str(e)}")
                raise
    
    def _load_schema(self, schema: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Load schema from file path or use dict directly."""
        if isinstance(schema, dict):
            return schema
        
        schema_path = Path(schema)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path) as f:
            return json.load(f)
    
    def _get_pydantic_model(self, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Create or retrieve cached Pydantic model from JSON schema.
        
        Args:
            schema: JSON schema dictionary
            
        Returns:
            Pydantic model class
        """
        # Create unique key for this schema
        schema_str = json.dumps(schema, sort_keys=True)
        schema_hash = hashlib.md5(schema_str.encode()).hexdigest()
        
        # Return cached model if exists
        if schema_hash in self.model_cache:
            return self.model_cache[schema_hash]
        
        # Create new model
        model = self._create_model_from_schema(schema)
        self.model_cache[schema_hash] = model
        return model
    
    def _create_model_from_schema(self, schema: Dict[str, Any]) -> Type[BaseModel]:
        """
        Convert JSON schema to Pydantic model dynamically.
        Handles nested objects, arrays, references, and complex types.
        
        Args:
            schema: JSON schema dictionary
            
        Returns:
            Pydantic model class
        """
        # Get schema properties
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        title = schema.get("title", "DynamicModel")
        
        # Sanitize title to ensure valid Python identifier
        import re
        title = re.sub(r'[^a-zA-Z0-9_]', '_', title)
        if title[0].isdigit():
            title = f"Model_{title}"
        
        # Build field definitions
        fields = {}
        for name, prop in properties.items():
            field_type = self._get_field_type(prop, name)
            is_required = name in required
            description = prop.get("description", "")
            
            # Handle field names with hyphens or other invalid Python identifiers
            field_name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
            if field_name[0].isdigit():
                field_name = f"field_{field_name}"
            # Handle fields starting with underscore (e.g., from $schema)
            if field_name.startswith('_'):
                field_name = f"field{field_name}"
            
            # Use alias if field name was modified
            if field_name != name:
                if is_required:
                    fields[field_name] = (field_type, Field(..., description=description, alias=name))
                else:
                    fields[field_name] = (field_type, Field(None, description=description, alias=name))
            else:
                if is_required:
                    fields[name] = (field_type, Field(..., description=description))
                else:
                    fields[name] = (field_type, Field(None, description=description))
        
        # Create and return model
        return create_model(title, **fields)
    
    def _get_field_type(self, prop: Dict[str, Any], field_name: str) -> Any:
        """
        Convert JSON schema property to Python type.
        
        Args:
            prop: Property definition from JSON schema
            field_name: Name of the field (for nested models)
            
        Returns:
            Python type for Pydantic field
        """
        prop_type = prop.get("type", "string")
        
        # Handle basic types
        if prop_type == "string":
            if "enum" in prop:
                # For enums, just use Union of Literal values instead of Enum class
                # This avoids issues with special characters in enum names
                from typing import Literal
                return Union[tuple(Literal[v] for v in prop["enum"])]
            return str
        elif prop_type == "integer":
            return int
        elif prop_type == "number":
            return float
        elif prop_type == "boolean":
            return bool
        elif prop_type == "null":
            return type(None)
        
        # Handle arrays
        elif prop_type == "array":
            items = prop.get("items", {})
            item_type = self._get_field_type(items, f"{field_name}Item")
            return List[item_type]
        
        # Handle objects (nested models)
        elif prop_type == "object":
            nested_properties = prop.get("properties", {})
            nested_required = prop.get("required", [])
            
            # Create nested model
            nested_fields = {}
            for nested_name, nested_prop in nested_properties.items():
                nested_type = self._get_field_type(nested_prop, f"{field_name}_{nested_name}")
                is_required = nested_name in nested_required
                description = nested_prop.get("description", "")
                
                # Handle field names with hyphens or other invalid Python identifiers
                import re
                nested_field_name = re.sub(r'[^a-zA-Z0-9_]', '_', nested_name)
                if nested_field_name[0].isdigit():
                    nested_field_name = f"field_{nested_field_name}"
                # Handle fields starting with underscore (e.g., from $schema)
                if nested_field_name.startswith('_'):
                    nested_field_name = f"field{nested_field_name}"
                
                # Use alias if field name was modified
                if nested_field_name != nested_name:
                    if is_required:
                        nested_fields[nested_field_name] = (nested_type, Field(..., description=description, alias=nested_name))
                    else:
                        nested_fields[nested_field_name] = (nested_type, Field(None, description=description, alias=nested_name))
                else:
                    if is_required:
                        nested_fields[nested_name] = (nested_type, Field(..., description=description))
                    else:
                        nested_fields[nested_name] = (nested_type, Field(None, description=description))
            
            # Sanitize model name
            import re
            model_name = re.sub(r'[^a-zA-Z0-9_]', '_', f"{field_name}Model")
            if model_name[0].isdigit():
                model_name = f"Model_{model_name}"
            return create_model(model_name, **nested_fields)
        
        # Handle union types (oneOf, anyOf)
        elif "oneOf" in prop or "anyOf" in prop:
            options = prop.get("oneOf", prop.get("anyOf", []))
            types = [self._get_field_type(opt, f"{field_name}Option{i}") for i, opt in enumerate(options)]
            return Union[tuple(types)]
        
        # Default to string for unknown types
        return str
    
    def _extract_with_retries(self, 
                            text: str, 
                            model: Type[BaseModel],
                            schema: Dict[str, Any]) -> BaseModel:
        """
        Extract information with automatic retries on failure.
        
        Args:
            text: Input text
            model: Pydantic model for validation
            schema: Original JSON schema for context
            
        Returns:
            Validated Pydantic model instance
        """
        # Create optimized prompt
        prompt = self._create_extraction_prompt(text, schema)
        
        # Determine which model to use
        use_model = self.model
        
        # Try primary model (GPT-4.1 if requested)
        if self.model == "gpt-4.1":
            try:
                return self.client.chat.completions.create(
                    model="gpt-4.1",
                    response_model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.UNIVERSAL_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_retries=self.max_retries,
                    temperature=self.temperature
                )
            except Exception as e:
                # Fallback to gpt-4o
                console.print(f"[yellow]Note: GPT-4.1 not available, using gpt-4o[/yellow]")
                use_model = "gpt-4o"
        
        # Use the selected model
        return self.client.chat.completions.create(
            model=use_model,
            response_model=model,
            messages=[
                {
                    "role": "system",
                    "content": self.UNIVERSAL_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_retries=self.max_retries,
            temperature=self.temperature
        )
    
    def _create_extraction_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """
        Create an optimized prompt for extraction.
        
        Args:
            text: Input text
            schema: JSON schema for context
            
        Returns:
            Formatted prompt string
        """
        # For large schemas, include a summary
        if len(json.dumps(schema)) > 10000:
            schema_summary = self._summarize_schema(schema)
            return f"""Extract structured information from the following text.

SCHEMA SUMMARY:
{schema_summary}

TEXT TO EXTRACT FROM:
{text}

Extract all relevant information according to the schema structure."""
        else:
            return f"""Extract structured information from the following text according to the schema.

TEXT TO EXTRACT FROM:
{text}

Extract all relevant information and ensure it matches the schema exactly."""
    
    def _summarize_schema(self, schema: Dict[str, Any]) -> str:
        """
        Create a concise summary of large schemas.
        
        Args:
            schema: JSON schema
            
        Returns:
            Human-readable schema summary
        """
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        summary = f"Schema: {schema.get('title', 'Document')}\n"
        summary += f"Required fields: {', '.join(required)}\n"
        summary += "Fields:\n"
        
        for name, prop in properties.items():
            field_type = prop.get("type", "unknown")
            description = prop.get("description", "")
            req_marker = " (required)" if name in required else ""
            summary += f"  - {name}: {field_type}{req_marker}"
            if description:
                summary += f" - {description[:50]}..."
            summary += "\n"
        
        return summary
    
    # Universal system prompt for all extractions
    UNIVERSAL_SYSTEM_PROMPT = """You are an expert at extracting structured information from unstructured text.

Your task is to analyze the given text and extract ALL information that maps to the provided JSON schema.

Follow these rules:
1. Extract ONLY information that is explicitly present in the text
2. Follow the schema structure EXACTLY - do not add or remove fields
3. Use null for missing optional fields - do not make up data
4. Ensure all required fields are populated from the text
5. Maintain data types exactly as specified in the schema
6. For ambiguous cases, make reasonable inferences based on context
7. If a required field cannot be found in the text, still provide a reasonable default or empty value

Remember: Your output must be valid according to the schema.

Special handling for enum fields: If a field has enum values and the content doesn't clearly match any option, choose the most appropriate one. For example, if 'type' field has options ['dataset', 'software'] and the content is about a research paper or model, choose 'software' as it represents intellectual work/code.""" 