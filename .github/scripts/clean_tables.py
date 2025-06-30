#!/usr/bin/env python3
"""
Remove border="1" from HTML tables in markdown files.
"""
import re


def clean_markdown_file(filepath):
    """Remove border='1' attribute from HTML tables."""
    with open(filepath, "r") as f:
        content = f.read()

    # Remove border="1" from table tags
    content = re.sub(r'<table\s+border="1"', "<table", content)

    # Write back the cleaned content
    with open(filepath, "w") as f:
        f.write(content)

    print(f"Removed border='1' from tables in {filepath}")


if __name__ == "__main__":
    clean_markdown_file("guide.md")
