"""
BIQL Query API - High-level interface for running BIQL queries

Provides a convenient API for executing queries with automatic formatting.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .dataset import BIDSDataset
from .evaluator import BIQLEvaluator
from .formatter import BIQLFormatter
from .parser import BIQLParser


class BIQLQuery:
    """High-level BIQL query interface with convenient methods"""

    def __init__(
        self, dataset: Union[str, Path, BIDSDataset], default_format: str = "json"
    ):
        """
        Initialize BIQL query interface

        Args:
            dataset: Path to BIDS dataset or BIDSDataset instance
            default_format: Default output format ('json', 'table', 'csv', 'tsv', 'paths', 'dataframe')
        """
        if isinstance(dataset, (str, Path)):
            self.dataset = BIDSDataset(dataset)
        else:
            self.dataset = dataset

        self.evaluator = BIQLEvaluator(self.dataset)
        self.default_format = default_format

    def run_query(
        self, query: str, format: Optional[str] = None
    ) -> Union[List[Dict[str, Any]], str, Any]:
        """
        Run a BIQL query and return formatted results

        Args:
            query: BIQL query string
            format: Output format override ('json', 'table', 'csv', 'tsv', 'paths', 'dataframe')
                   If None, uses default_format from initialization

        Returns:
            - List[Dict] for 'json' format
            - str for 'table', 'csv', 'tsv', 'paths' formats
            - DataFrame for 'dataframe' format
        """
        # Parse and evaluate query
        parser = BIQLParser.from_string(query)
        parsed_query = parser.parse()
        results = self.evaluator.evaluate(parsed_query)

        # Determine output format
        output_format = format if format is not None else self.default_format

        # Handle DataFrame format specially
        if output_format == "dataframe":
            return self._to_dataframe(results)

        # Handle JSON format (return raw results)
        if output_format == "json":
            return results

        # Use standard formatter for other formats
        return BIQLFormatter.format(results, output_format)

    def _to_dataframe(self, results: List[Dict[str, Any]]) -> Any:
        """Convert results to pandas DataFrame"""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame output format. "
                "Install with: pip install pandas"
            )

        if not results:
            return pd.DataFrame()

        # Handle nested data by flattening or converting to strings
        flattened_results = []
        for result in results:
            flattened = {}
            for key, value in result.items():
                if isinstance(value, (dict, list)):
                    # Convert complex structures to strings for DataFrame compatibility
                    if isinstance(value, dict) and value:
                        # For metadata and participants, show key info
                        if key == "metadata":
                            # Show a few key metadata fields
                            meta_summary = []
                            for mk, mv in value.items():
                                if mk in [
                                    "RepetitionTime",
                                    "EchoTime",
                                    "FlipAngle",
                                    "TaskName",
                                ]:
                                    meta_summary.append(f"{mk}={mv}")
                            flattened[key] = (
                                "; ".join(meta_summary) if meta_summary else str(value)
                            )
                        elif key == "participants":
                            # Show key participant info
                            parts_summary = []
                            for pk, pv in value.items():
                                if pk in ["age", "sex", "group", "site"]:
                                    parts_summary.append(f"{pk}={pv}")
                            flattened[key] = (
                                "; ".join(parts_summary)
                                if parts_summary
                                else str(value)
                            )
                        else:
                            flattened[key] = str(value)
                    elif isinstance(value, list):
                        # Convert arrays to comma-separated strings
                        flattened[key] = (
                            ", ".join(str(v) for v in value) if value else ""
                        )
                    else:
                        flattened[key] = str(value)
                else:
                    flattened[key] = value
            flattened_results.append(flattened)

        return pd.DataFrame(flattened_results)

    def get_subjects(self) -> List[str]:
        """Get all subjects in the dataset"""
        return sorted(list(self.dataset.get_subjects()))

    def get_datatypes(self) -> List[str]:
        """Get all datatypes in the dataset"""
        return sorted(list(self.dataset.get_datatypes()))

    def get_entities(self) -> Dict[str, List[str]]:
        """Get all available entities and their values"""
        entities = {}
        for file in self.dataset.files:
            for entity, value in file.entities.items():
                if entity not in entities:
                    entities[entity] = set()
                if value is not None:
                    entities[entity].add(value)

        # Convert sets to sorted lists
        return {entity: sorted(list(values)) for entity, values in entities.items()}

    def dataset_stats(self) -> Dict[str, Any]:
        """Get basic dataset statistics"""
        results = self.run_query("SELECT datatype, COUNT(*) GROUP BY datatype")

        stats = {
            "total_files": len(self.dataset.files),
            "total_subjects": len(self.dataset.participants),
            "files_by_datatype": {
                r["datatype"]: r["count"] for r in results if r.get("datatype")
            },
            "subjects": self.get_subjects(),
            "datatypes": self.get_datatypes(),
        }

        return stats


def create_query_engine(
    dataset: Union[str, Path, BIDSDataset], default_format: str = "json"
) -> BIQLQuery:
    """
    Convenience function to create a BIQL query engine

    Args:
        dataset: Path to BIDS dataset or BIDSDataset instance
        default_format: Default output format

    Returns:
        BIQLQuery instance ready for use
    """
    return BIQLQuery(dataset, default_format)
