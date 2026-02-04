# Contributing to BabySleepViz

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/gototen/baby-sleep-viz.git
   cd baby-sleep-viz
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Set up pre-commit hooks (runs linting automatically before each commit):
   ```bash
   pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

We use `ruff` for linting and formatting. Use these commands:

```bash
make fmt      # Auto-fix all linting/formatting issues
make lint     # Check for issues (no auto-fix)
make test     # Run tests
make check    # Run lint + test
```

Or run ruff directly:

```bash
ruff check --fix src/ tests/    # Auto-fix linting
ruff format src/ tests/          # Auto-format code
```

### Pre-commit Hooks

If you installed pre-commit hooks (step 4 above), linting runs automatically on every commit. If there are issues:
1. The commit will fail
2. Files are auto-fixed
3. Just `git add .` and commit again

**Tip:** If your commit keeps failing, just run `make fmt` to fix everything, then commit.

## Adding Support for New Baby Tracking Apps

One of the most valuable contributions is adding support for other baby tracking apps.

### Steps to add a new data source:

1. **Get a sample export** from the app (use anonymized/synthetic data)

2. **Create a config file** in `configs/`:
   ```yaml
   # configs/your_app.yaml
   name: your_app
   description: "Your App Name"
   
   columns:
     type: EventType      # Column containing event type
     start: StartTime     # Column with start timestamp
     end: EndTime         # Column with end timestamp
   
   event_types:
     sleep: Sleep         # Value that indicates sleep events
     feed: Feeding        # Value that indicates feed events
     meds: Medication     # Value that indicates medication events
   
   med_name_column: MedicationName  # Column with medication names
   ```

3. **Test with sample data**:
   ```bash
   babysleepviz sample_export.csv --day-zero 2024-01-01 -c configs/your_app.yaml -o test_output.png
   ```

4. **Add documentation** to README about the new source

5. **Submit a PR** with:
   - The new config file
   - Updated README section listing the new app
   - Any code changes needed for parsing edge cases

## Reporting Issues

When reporting bugs, please include:
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Sample data (anonymized) if relevant

## Feature Requests

Feature requests are welcome! Please:
- Check existing issues first
- Describe the use case
- Suggest an implementation approach if possible

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Add/update tests as needed
4. Update documentation
5. Ensure CI passes
6. Request review

### PR Title Format

Use conventional commit style:
- `feat: add support for BabyTracker app`
- `fix: correct midnight boundary calculation`
- `docs: update installation instructions`
- `test: add integration tests for visualization`

## Code of Conduct

Be respectful and inclusive. We're all parents (or friends of parents) trying to understand baby sleep patterns!

## Questions?

Open an issue with the "question" label or start a discussion.
