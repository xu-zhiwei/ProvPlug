from . import darpa_e3
from . import optc
from graph_construction import *


def parse(mode: str, **kwargs) -> None:
    """Unified parser interface for different provenance formats

    Args:
        mode: Parser mode, either 'darpa_e3' or 'optc'
        **kwargs: Arguments specific to each parser mode

    For 'darpa_e3' mode:
        - archive_file: Path to the tar.gz archive file
        - data_files: List of data file paths to process
        - edge_files: List of edge file paths to process

    For 'optc' mode:
        - input_filename: Path to input JSONL file
        - output_filename: Path to output JSONL file

    Raises:
        ValueError: If mode is not recognized
    """
    if mode == "darpa_e3":
        darpa_e3.parse(
            data_files=kwargs.get("data_files", []),
            edge_files=kwargs.get("edge_files", []),
        )
    elif mode == "optc":
        optc.parse(
            input_filename=kwargs.get("input_filename"),
            output_filename=kwargs.get("output_filename"),
        )
    else:
        raise ValueError(
            f"Unknown parse mode: {mode}. Supported modes: 'darpa_e3', 'optc'"
        )


__all__ = [
    "parse",
    "darpa_e3",
    "optc",
    "build_undirected_graph",
    "build_directed_graph",
]
