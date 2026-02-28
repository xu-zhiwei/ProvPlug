# Parse Audit Log with `parse.py`

`parse.py` is a command-line tool for parsing audit log data in different formats. Currently, ProvPlug supports two modes: `darpa_e3` and `optc`.

## Basic Usage

```bash
python src/parse.py <mode> [options]
```

## Usage Details

### 1. DARPA E3 Mode

Used for parsing audit log data in DARPA E3 format.

**Command Format:**
```bash
python src/parse.py darpa_e3 --data-files <data_files> --edge-files <edge_files>
```

**Arguments:**
- `--data-files` (required): List of data file paths (supports multiple files), which are utilized to extract `uuids` for filtering useful edges.
- `--edge-files` (required): List of edge file paths (supports multiple files)

**Example:**
```bash
python src/parse.py darpa_e3 \
  --data-files /path/to/data1.json /path/to/data2.json \
  --edge-files /path/to/edges1.json /path/to/edges2.json
```

### 2. OPTC Mode

Used for parsing audit log data in OPTC format.

**Command Format:**
```bash
python src/parse.py optc --input-filename <input_file> --output-filename <output_file>
```

**Arguments:**
- `--input-filename` (required): Path to the input file
- `--output-filename` (required): Path to the output file

**Example:**
```bash
python src/parse.py optc \
  --input-filename /path/to/input.txt \
  --output-filename /path/to/output.json
```

## Parsed Results

After parsing, the results will be saved in the specified output files in JSON lines format, containing the structured representation of the audit logs sorted in chronological order. The JSON format is unified across different modes for easier downstream processing, whose example is illustrated as follows:

```json
{
  "subject": "firefox.exe",
  "event": "write",
  "object": "/home/admin/profile"
}