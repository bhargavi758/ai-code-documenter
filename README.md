# ai-code-documenter

CLI that reads Python and TypeScript codebases and generates docs from the code structure. Parses Python with the `ast` module and TypeScript with regex. No AI APIs involved despite the name.

## install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

## usage

```bash
docgen analyze ./my-project --output docs/
docgen readme ./my-project --output README.md
docgen stats ./my-project
docgen check ./my-project --docs docs/   # checks if docs are stale
```

Extracts classes, functions, imports, type annotations. Calculates cyclomatic complexity. Maps dependencies between modules and catches circular imports. Outputs markdown or JSON.

## tests

```bash
pytest
pytest --cov=src --cov-report=term-missing
```

Python 3.10+, Click, Rich

## todo

- swap regex for tree-sitter on the TS side
- watch mode for auto-regen on file changes
