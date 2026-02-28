import gdown
import gzip
import io
from tqdm import tqdm


OPTC_GOOGLE_DRIVE_URLS = [
    "https://drive.google.com/file/d/1HFSyvmgH0jvdnnnTdKfWRjZYOrLWoIkv/view?usp=drive_link",
    "https://drive.google.com/file/d/1pJLxJsDV8sngiedbfVajMetczIgM3PQd/view?usp=drive_link",
    "https://drive.google.com/file/d/1fRQqc68r8-z5BL7H_eAKIDOeHp7okDuM/view?usp=drive_link",
    "https://drive.google.com/file/d/1VfyGr8wfSe8LBIHBWuYBlU8c2CyEgO5C/view?usp=drive_link",
    "https://drive.google.com/file/d/10N9ZPolq_L8HivBqzf_jFKbwjSxddsZp/view?usp=drive_link",
    "https://drive.google.com/file/d/1xIr8gw-4zc8ESjUpYtrFsbOwhPGUSd15/view?usp=drive_link",
    "https://drive.google.com/file/d/1PvlCp2oQaxEBEFGSQWfcFVj19zLOe7yH/view?usp=drive_link",
]


def download_datasets():
    """Download all OPTC dataset files."""
    for download_url in OPTC_GOOGLE_DRIVE_URLS:
        gdown.download(download_url, quiet=False, use_cookies=False, fuzzy=True)


def extract_logs_from_archive(archive_filepath, host_id):
    """
    Extract logs for a specific host from compressed log archive.

    Args:
        archive_filepath (str): Path to the compressed log file
        host_id (str): Host ID
    """
    search_pattern = f"../SysClient{host_id}"
    output_filepath = f"../SysClient{host_id}.systemia.com.txt"

    with gzip.open(archive_filepath, "rt", encoding="utf-8") as gz_file:
        with open(output_filepath, "ab") as output_file:
            buffered_writer = io.BufferedWriter(output_file)
            for line in gz_file:
                if search_pattern in line:
                    buffered_writer.write(line.encode("utf-8"))
            buffered_writer.flush()


def prepare_test_dataset():
    """Prepare test dataset by extracting logs for all hosts from log files."""
    log_file_records = [
        ("AIA-201-225.ecar-2019-12-08T11-05-10.046.json.gz", "0201"),
        ("AIA-201-225.ecar-last.json.gz", "0201"),
        ("AIA-501-525.ecar-2019-11-17T04-01-58.625.json.gz", "0501"),
        ("AIA-501-525.ecar-last.json.gz", "0501"),
        ("AIA-51-75.ecar-last.json.gz", "0051"),
    ]

    for log_filename, host_id in tqdm(
        log_file_records, desc="Extracting logs", unit="file"
    ):
        extract_logs_from_archive(log_filename, host_id)


if __name__ == "__main__":
    download_datasets()
    prepare_test_dataset()