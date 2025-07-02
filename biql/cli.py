"""
Command Line Interface for BIDS Query Language (BIQL)

Provides a CLI for executing BIQL queries against BIDS datasets.
"""

import argparse
import sys
from pathlib import Path

from .dataset import BIDSDataset
from .evaluator import BIQLEvaluator
from .formatter import BIQLFormatter
from .parser import BIQLParseError, BIQLParser

try:
    import readline

    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog="biql",
        description="BIDS Query Language (BIQL) - Query BIDS datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find all T1w files
  biql "suffix=T1w"

  # Find functional files for subject 01
  biql "sub=01 AND datatype=func"

  # Complex query with metadata
  biql "task=rest AND metadata.RepetitionTime<3.0"

  # Select specific fields
  biql "SELECT sub, ses, filepath WHERE datatype=anat"

  # Output as table
  biql "sub=01" --format table

  # Group by subject
  biql "SELECT sub, COUNT(*) GROUP BY sub"

  # Range queries
  biql "run=[1:5] AND task=nback"

  # Pattern matching
  biql "sub=control* OR task~=/mem.*/"

  # Interactive shell (default when no query provided)
  biql
  biql --dataset /path/to/dataset
        """,
    )

    parser.add_argument(
        "query",
        nargs="?",
        help="BIQL query string (use quotes to avoid shell interpretation)",
    )

    parser.add_argument(
        "--dataset",
        "-d",
        default=".",
        help="Path to BIDS dataset (default: current directory)",
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "table", "csv", "tsv", "paths"],
        default="json",
        help="Output format (default: json)",
    )

    parser.add_argument("--output", "-o", help="Output file (default: stdout)")

    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate query syntax, don't execute",
    )

    parser.add_argument(
        "--show-entities",
        action="store_true",
        help="Show available entities in the dataset and exit",
    )

    parser.add_argument(
        "--show-stats", action="store_true", help="Show dataset statistics and exit"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 0.3.0")

    return parser


def show_dataset_stats(dataset: BIDSDataset) -> None:
    """Show dataset statistics"""
    print(f"Dataset: {dataset.root}")
    print(f"Total files: {len(dataset.files)}")
    print(f"Subjects: {len(dataset.get_subjects())}")
    print(f"Sessions: {len(dataset.get_sessions())}")
    print(f"Datatypes: {', '.join(sorted(dataset.get_datatypes()))}")
    print(f"Tasks: {', '.join(sorted(dataset.get_tasks()))}")

    if dataset.dataset_description:
        desc = dataset.dataset_description
        if "Name" in desc:
            print(f"Name: {desc['Name']}")
        if "BIDSVersion" in desc:
            print(f"BIDS Version: {desc['BIDSVersion']}")


def show_dataset_entities(dataset: BIDSDataset) -> None:
    """Show available entities in the dataset"""
    entities = dataset.get_entities()
    print("Available entities:")
    for entity in sorted(entities):
        print(f"  {entity}")


def setup_readline():
    """Setup readline for better command line editing"""
    if not HAS_READLINE:
        return

    # Enable tab completion
    readline.set_completer_delims(" \t\n`~!@#$%^&*()=+[{]}\\|;:'\",<>?")
    readline.parse_and_bind("tab: complete")

    # Enable history
    try:
        import os

        history_file = os.path.expanduser("~/.biql_history")
        readline.read_history_file(history_file)
        readline.set_history_length(1000)

        # Save history on exit
        import atexit

        atexit.register(readline.write_history_file, history_file)
    except (FileNotFoundError, PermissionError):
        pass


def interactive_shell(dataset: BIDSDataset, debug: bool = False) -> None:
    """Start interactive BIQL shell"""
    setup_readline()

    print("BIQL Interactive Shell")
    print(f"Dataset: {dataset.root}")
    print(f"Files: {len(dataset.files)}")
    print("Type 'help' for commands, 'quit' or Ctrl+C to exit\n")

    evaluator = BIQLEvaluator(dataset)

    while True:
        try:
            # Get query from user
            query_str = input("biql> ").strip()

            if not query_str:
                continue

            # Handle special commands
            if query_str.lower() in ("quit", "exit", "q"):
                break
            elif query_str.lower() == "help":
                print_interactive_help()
                continue
            elif query_str.lower() == "stats":
                show_dataset_stats(dataset)
                continue
            elif query_str.lower() == "entities":
                show_dataset_entities(dataset)
                continue
            elif query_str.lower().startswith("format "):
                format_type = query_str[7:].strip()
                if format_type in ["json", "table", "csv", "tsv", "paths"]:
                    print(f"Default format set to: {format_type}")
                    # Store format preference in evaluator
                    evaluator._default_format = format_type
                else:
                    print(f"Invalid format: {format_type}")
                    print("Available formats: json, table, csv, tsv, paths")
                continue

            # Execute query
            try:
                parser = BIQLParser.from_string(query_str)
                query = parser.parse()

                if debug:
                    print(f"Parsed: {query}")

                results = evaluator.evaluate(query)

                # Determine format
                format_type = query.format or getattr(
                    evaluator, "_default_format", "json"
                )

                # Format and display results
                original_files = (
                    evaluator.get_original_matching_files()
                    if format_type == "paths"
                    else None
                )

                formatted = BIQLFormatter.format(results, format_type, original_files)
                print(formatted)

                if results:
                    print(f"\n{len(results)} result{'s' if len(results) != 1 else ''}")

            except BIQLParseError as e:
                print(f"Syntax error: {e}")
            except Exception as e:
                print(f"Error: {e}")
                if debug:
                    import traceback

                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit")
        except EOFError:
            print("\nGoodbye!")
            break


def print_interactive_help():
    """Print help for interactive mode"""
    help_text = """
Interactive BIQL Shell Commands:

Query Examples:
  suffix=T1w                    - Find T1w files
  sub=01 AND datatype=func      - Functional files for sub-01
  SELECT sub, ses WHERE task=rest - Select specific fields

Special Commands:
  help                          - Show this help
  stats                         - Show dataset statistics
  entities                      - Show available entities
  format <type>                 - Set default output format
  quit, exit, q                 - Exit shell

Formats: json, table, csv, tsv, paths

Keyboard Shortcuts:
  ↑/↓                          - Command history
  Ctrl+A/E                     - Beginning/end of line
  Ctrl+W                       - Delete word backward
  Alt+Backspace                - Delete word backward
  Tab                          - Auto-completion (if available)
"""
    print(help_text)


def validate_query(query_str: str) -> bool:
    """Validate query syntax without executing"""
    try:
        parser = BIQLParser.from_string(query_str)
        query = parser.parse()
        print("Query syntax is valid.")
        if query.select_clause:
            print(f"SELECT: {[item[0] for item in query.select_clause.items]}")
        if query.where_clause:
            print("WHERE clause present")
        if query.group_by:
            print(f"GROUP BY: {query.group_by}")
        if query.order_by:
            print(f"ORDER BY: {query.order_by}")
        if query.format:
            print(f"FORMAT: {query.format}")
        return True
    except BIQLParseError as e:
        print(f"Query syntax error: {e}", file=sys.stderr)
        return False


def main() -> int:
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Check if dataset path exists
        dataset_path = Path(args.dataset).resolve()
        if not dataset_path.exists():
            print(
                f"Error: Dataset path does not exist: {dataset_path}", file=sys.stderr
            )
            return 1

        # Load dataset
        if args.debug:
            print(f"Loading dataset from: {dataset_path}", file=sys.stderr)

        try:
            dataset = BIDSDataset(dataset_path)
        except Exception as e:
            print(f"Error loading dataset: {e}", file=sys.stderr)
            return 1

        if args.debug:
            print(f"Found {len(dataset.files)} files", file=sys.stderr)

        # Handle special modes
        if args.show_stats:
            show_dataset_stats(dataset)
            return 0

        if args.show_entities:
            show_dataset_entities(dataset)
            return 0

        # If no query provided, start interactive mode
        if not args.query:
            interactive_shell(dataset, args.debug)
            return 0

        # Validate query syntax
        if args.validate_only:
            return 0 if validate_query(args.query) else 1

        # Parse query
        try:
            parser = BIQLParser.from_string(args.query)
            query = parser.parse()
        except BIQLParseError as e:
            print(f"Query syntax error: {e}", file=sys.stderr)
            return 1

        if args.debug:
            print(f"Parsed query: {query}", file=sys.stderr)

        # Evaluate query
        try:
            evaluator = BIQLEvaluator(dataset)
            results = evaluator.evaluate(query)
        except Exception as e:
            print(f"Query evaluation error: {e}", file=sys.stderr)
            if args.debug:
                import traceback

                traceback.print_exc()
            return 1

        if args.debug:
            print(f"Found {len(results)} results", file=sys.stderr)

        # Determine output format
        format_type = query.format if query.format else args.format

        # Format and output results
        try:
            # Get original files for paths formatter
            original_files = (
                evaluator.get_original_matching_files()
                if format_type == "paths"
                else None
            )
            formatted = BIQLFormatter.format(results, format_type, original_files)

            if args.output:
                # Write to file
                with open(args.output, "w") as f:
                    f.write(formatted)
                if args.debug:
                    print(f"Output written to: {args.output}", file=sys.stderr)
            else:
                # Write to stdout
                print(formatted)

        except Exception as e:
            print(f"Output formatting error: {e}", file=sys.stderr)
            return 1

        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if args.debug:
            import traceback

            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
