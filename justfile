# storymap justfile
# requires: just (https://github.com/casey/just)
#           pipenv (https://pipenv.pypa.io)
# for release: gh (GitHub CLI)

pipenv := require("pipenv")
gh     := require("gh")
out_dir := "out"

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

# Generate HTML output from a markdown file (→ out/)
run file:
    mkdir -p {{out_dir}}
    {{pipenv}} run storymap {{file}} --output {{out_dir}}

# Generate PDF output from a markdown file (→ out/)
run-pdf file:
    mkdir -p {{out_dir}}
    {{pipenv}} run storymap {{file}} --format pdf --output {{out_dir}}

# Generate both HTML and PDF from a markdown file (→ out/)
run-both file:
    mkdir -p {{out_dir}}
    {{pipenv}} run storymap {{file}} --format both --output {{out_dir}}

# Generate output in a custom directory
run-out file dir:
    mkdir -p {{dir}}
    {{pipenv}} run storymap {{file}} --output {{dir}}

# Remove generated out/ folder
clean:
    rm -rf {{out_dir}}

# Remove build artifacts including egg-info
clean-build:
    rm -rf dist/ build/
    find . -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} +

# Remove virtualenv and lock file
clean-env:
    {{pipenv}} --rm
    rm -f Pipfile.lock

# Build distribution packages (sdist + wheel)
build: clean-build
    {{pipenv}} run pip install --quiet build
    {{pipenv}} run python -m build

# Upload to PyPI (requires ~/.pypirc or TWINE_* env vars)
publish: build
    {{pipenv}} run pip install --quiet twine
    {{pipenv}} run twine upload dist/*

# Upload to TestPyPI for a dry run
publish-test: build
    {{pipenv}} run pip install --quiet twine
    {{pipenv}} run twine upload --repository testpypi dist/*

# Create a git tag and GitHub release for the current version
release: build
    #!/usr/bin/env bash
    set -euo pipefail
    version=$({{pipenv}} run python -c "from importlib.metadata import version; print(version('storymap'))")
    tag="v${version}"
    echo "Releasing ${tag}..."
    git tag "${tag}"
    git push origin "${tag}"
    {{ gh }} release create "${tag}" dist/* \
        --title "storymap ${tag}" \
        --generate-notes

# Show the path to the bundled default template
template-path:
    {{pipenv}} run python -c "from pathlib import Path; import storymap; print(Path(storymap.__file__).parent / 'templates' / 'default.html.j2')"
