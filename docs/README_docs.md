# BIQL Documentation

This directory contains the documentation for BIQL, automatically built and deployed to GitHub Pages.

## Files

- `guide.ipynb` - Interactive Jupyter notebook tutorial (source of truth)
- `tutorial.md` - Auto-generated markdown from executed notebook
- `language.md` - Complete language reference
- `index.md` - Documentation homepage

## Automated Tutorial Generation

The tutorial is automatically generated from `guide.ipynb` using GitHub Actions:

1. **Trigger**: When `guide.ipynb` changes on main branch
2. **Process**:
   - Clones bids-examples dataset for live data
   - Executes all notebook cells with real BIQL queries
   - Converts executed notebook to `tutorial.md`
   - Commits the updated tutorial back to the repository
3. **Result**: Live, always-up-to-date tutorial with actual query results

## Local Development

To work on the tutorial locally:

```bash
# Install dependencies
pip install jupyter nbconvert pandas
pip install -e .  # Install BIQL from source

# Clone test data
mkdir -p example-notebooks
cd example-notebooks
git clone https://github.com/bids-standard/bids-examples.git

# Execute notebook locally
jupyter nbconvert --to notebook --execute --inplace guide.ipynb

# Convert to markdown for preview
jupyter nbconvert --to markdown guide.ipynb --output tutorial.md
```

## Jekyll Documentation

The site uses Jekyll with the `just-the-docs` theme. Key files:

- `_config.yml` - Jekyll configuration
- `Gemfile` - Ruby dependencies
- Front matter in `.md` files controls navigation

The documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch.
