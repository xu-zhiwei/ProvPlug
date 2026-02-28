import gdown
import os
import tarfile

# DARPA TRACE
urls = [
    "https://drive.google.com/file/d/1GG1aUnPjjzzdbxznVTN8X6oVfA-K4oIV/view?usp=drive_link"
]

# DARPA THEIA
urls += [
    "https://drive.google.com/file/d/10cecNtR3VsHfV0N-gNEeoVeB89kCnse5/view?usp=drive_link",
    "https://drive.google.com/file/d/1Kadc6CUTb4opVSDE4x6RFFnEy0P1cRp0/view?usp=drive_link",
]

# DARPA CADETS
urls += [
    "https://drive.google.com/file/d/1AcWrYiBmgAqp7DizclKJYYJJBQbnDMfb/view?usp=drive_link",
    "https://drive.google.com/file/d/1EycO23tEvZVnN3VxOHZ7gdbSCwqEZTI1/view?usp=drive_link",
]

# DARPA FIVEDIRECTIONS
urls += [
    "https://drive.google.com/file/d/1BeP80zUUmm4eZl0UuU43PsKNkl_xgskj/view?usp=drive_link"
]


def download_datasets():
    """Download all DARPA E3 dataset files."""
    for url in urls:
        gdown.download(url, quiet=False, use_cookies=False, fuzzy=True)


def extract_archive(archive_file: str) -> None:
    """Extract tar.gz archive file."""
    if not os.path.exists(archive_file):
        print(f"Error: Archive file {archive_file} not found")
        return

    print(f"Extracting {archive_file}...")
    try:
        with tarfile.open(archive_file, 'r:gz') as tar:
            tar.extractall()
        print(f"Successfully extracted {archive_file}")
    except Exception as e:
        print(f"Error extracting {archive_file}: {e}")


if __name__ == "__main__":
    # Download all datasets
    download_datasets()

    # Extract archives
    # Update archive filenames based on downloaded files
    archive_files = [
        "ta1-trace-e3-official-1.json.tar.gz",
    ]

    for archive_file in archive_files:
        extract_archive(archive_file)
