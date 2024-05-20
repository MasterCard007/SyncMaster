
# SyncMaster

SyncMaster is a Python-based file synchronization tool that allows you to efficiently synchronize files between two directories. It supports concurrent file operations and provides detailed logging.

## Features

- **Logging**: Provides detailed logging of synchronization operations.
- **Directory Traversal**: Recursively retrieves all files from the specified directories.
- **File Hashing**: Uses SHA-256 to compute file hashes for comparison.
- **Concurrent Operations**: Utilizes concurrent processing to speed up synchronization.

## Requirements

- Python 3.x
- `humanize` module

## Installation

1. Clone the repository or download the script.
2. Install the required Python module:

```bash
pip install humanize
```

## Usage

1. Run the script:

```bash
python SyncMaster.py
```

2. Follow the prompts to enter the source and target directory paths.

## Functions

- `setup_logging()`: Configures the logging format and level.
- `get_folder_path(prompt)`: Prompts the user for a valid directory path.
- `get_all_files(directory)`: Returns a list of all files in a directory, excluding hidden files.
- `file_hash(file_path)`: Computes the SHA-256 hash of a file.
- `compare_and_sync(source, target, executor)`: Compares files in the source and target directories and synchronizes them using concurrent operations.

## License

This project is licensed under the MIT License.
