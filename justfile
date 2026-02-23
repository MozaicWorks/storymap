# storymap justfile
# requires: just (https://github.com/casey/just)
#           pipenv (https://pipenv.pypa.io)

pipenv := require("pipenv")

# List available recipes
default:
    @just --list

# Install all dependencies and the package in editable mode
install:
    {{pipenv}} install --dev
    {{pipenv}} run pip install -e .

# Run all tests
test:
    {{pipenv}} run pytest

# Run tests with verbose output
test-v:
    {{pipenv}} run pytest -v

# Run tests for a specific module (e.g: just test-module model)
test-module module:
    {{pipenv}} run pytest tests/test_{{module}}.py -v

# Generate HTML output from a markdown file
run file:
    {{pipenv}} run storymap {{file}}

# Generate PDF output from a markdown file
run-pdf file:
    {{pipenv}} run storymap {{file}} --format pdf

# Generate both HTML and PDF from a markdown file
run-both file:
    {{pipenv}} run storymap {{file}} --format both

# Generate output in a specific directory
run-out file dir:
    {{pipenv}} run storymap {{file}} --output {{dir}}

# Remove generated output files
clean:
    find . -name "*.html" -not -path "./.venv/*" -delete
    find . -name "*.pdf" -not -path "./.venv/*" -delete

# Remove virtualenv and lock file
clean-env:
    {{pipenv}} --rm
    rm -f Pipfile.lock

# Show the path to the bundled default template
template-path:
    {{pipenv}} run python -c "from pathlib import Path; import storymap; print(Path(storymap.__file__).parent / 'templates' / 'default.html.j2')"
