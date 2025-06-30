#!/usr/bin/env python3
"""
Clean up pandas dataframe HTML output and convert to markdown tables
for better integration with Just the Docs theme.
"""
import re


def html_table_to_markdown(match):
    """Convert HTML table to markdown table format."""
    html_table = match.group(0)

    # Extract headers
    thead_match = re.search(r"<thead>.*?</thead>", html_table, re.DOTALL)
    tbody_match = re.search(r"<tbody>.*?</tbody>", html_table, re.DOTALL)

    if not thead_match or not tbody_match:
        return html_table  # Return original if parsing fails

    # Extract header cells
    headers = re.findall(r"<th[^>]*>(.*?)</th>", thead_match.group(0))
    headers = [h.strip() for h in headers if h.strip() and h.strip() != ""]

    # Extract data rows
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbody_match.group(0), re.DOTALL)

    markdown_lines = []

    if headers:
        # Create header row
        markdown_lines.append("| " + " | ".join(headers) + " |")
        markdown_lines.append("|" + "---|" * len(headers))

    # Create data rows
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row)
        cells = [c.strip() for c in cells]
        if cells:
            markdown_lines.append("| " + " | ".join(cells) + " |")

    return "\n\n" + "\n".join(markdown_lines) + "\n\n"


def clean_markdown_file(filepath):
    """Clean up the markdown file by removing pandas styling and converting tables."""
    with open(filepath, "r") as f:
        content = f.read()

    # Remove pandas styling divs
    content = re.sub(
        r"<div>\s*<style scoped[^>]*>.*?</style>", "", content, flags=re.DOTALL
    )

    # Convert HTML tables to markdown tables
    content = re.sub(
        r'<div class="table-wrapper">.*?</div>\s*</div>',
        html_table_to_markdown,
        content,
        flags=re.DOTALL,
    )

    # Write back the cleaned content
    with open(filepath, "w") as f:
        f.write(content)

    print(f"Cleaned up dataframe styling in {filepath}")


if __name__ == "__main__":
    clean_markdown_file("guide.md")
