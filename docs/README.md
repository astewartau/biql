# BIQL Documentation

This directory contains the Jekyll-based documentation for BIDS Query Language (BIQL).

## Setting up GitHub Pages

1. **Enable GitHub Pages** in your repository settings:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` (or `master`)
   - Folder: `/docs`

2. **Update URLs** in `_config.yml`:
   ```yaml
   url: "https://astewartau.github.io"
   baseurl: "/your-repo-name"
   repository: "astewartau/your-repo-name"
   ```

3. **GitHub Actions** (recommended):
   - The `.github/workflows/docs.yml` file will automatically build and deploy
   - Alternatively, use GitHub's built-in Jekyll support

## Local Development

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Then visit `http://localhost:4000`

## Theme

Using [Just the Docs](https://just-the-docs.github.io/just-the-docs/) theme for professional documentation appearance.