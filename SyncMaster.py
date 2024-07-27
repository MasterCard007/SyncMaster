import os
import shutil
import hashlib
from pathlib import Path
import logging
import concurrent.futures
import multiprocessing
from tqdm import tqdm
import platform

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_folder_path(prompt):
    path = input(prompt)
    while not Path(path).is_dir():
        print("Invalid path. Please enter a valid folder path.")
        path = input(prompt)
    return Path(path)

def get_all_files(directory):
    return [f for f in directory.rglob('*') if f.is_file() and not f.name.startswith('.')]

def file_hash(file_path, chunk_size=131072):  # Larger chunk size for better performance
    hasher = hashlib.blake2b()
    with file_path.open('rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

def compare_partial_content(file1, file2, chunk_size=131072):  # Larger chunk size for better performance
    with file1.open('rb') as f1, file2.open('rb') as f2:
        for _ in range(2):  # Compare the first 2 chunks (256KB)
            if f1.read(chunk_size) != f2.read(chunk_size):
                return False
    return True

def compare_files(src_file, tgt_file):
    if tgt_file:
        src_stat = src_file.stat()
        tgt_stat = tgt_file.stat()
        if src_stat.st_size != tgt_stat.st_size:
            return False
        if src_stat.st_mtime == tgt_stat.st_mtime:
            return True
        if compare_partial_content(src_file, tgt_file):
            return True
        return file_hash(src_file) == file_hash(tgt_file)
    return False

def check_free_space(target, total_size):
    stat = shutil.disk_usage(target)
    free_space_after_sync = stat.free - total_size
    free_space_percentage = (free_space_after_sync / stat.total) * 100
    return free_space_after_sync, free_space_percentage

def format_size(size):
    if size >= 1 << 30:
        return f"{size / (1 << 30):.2f} GiB"
    return f"{size / (1 << 20):.2f} MiB"

def compare_and_sync(source, target, executor):
    source_files = get_all_files(source)
    target_files = get_all_files(target)
    target_files_dict = {f.relative_to(target): f for f in target_files}
    source_files_dict = {f.relative_to(source): f for f in source_files}

    common_files = set()
    to_transfer = []
    to_transfer_from_target = []
    total_size = 0
    total_size_target = 0

    future_to_file = {executor.submit(compare_files, src_file, target_files_dict.get(src_file.relative_to(source))): src_file for src_file in source_files}

    for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(source_files), desc="Comparing files from source to target"):
        src_file = future_to_file[future]
        try:
            if future.result():
                common_files.add(src_file.relative_to(source))
            else:
                to_transfer.append(src_file)
                total_size += src_file.stat().st_size
        except Exception as e:
            logging.error(f"Error processing {src_file}: {e}")

    future_to_file_target = {executor.submit(compare_files, tgt_file, source_files_dict.get(tgt_file.relative_to(target))): tgt_file for tgt_file in target_files}

    for future in tqdm(concurrent.futures.as_completed(future_to_file_target), total=len(target_files), desc="Comparing files from target to source"):
        tgt_file = future_to_file_target[future]
        try:
            if not future.result() and tgt_file.relative_to(target) not in common_files:
                to_transfer_from_target.append(tgt_file)
                total_size_target += tgt_file.stat().st_size
        except Exception as e:
            logging.error(f"Error processing {tgt_file}: {e}")

    # Show information and ask for confirmation
    print(f"Total size to transfer from source to target: {format_size(total_size)}")
    print(f"Number of files to transfer from source to target: {len(to_transfer)}")
    print(f"Total size to transfer from target to source: {format_size(total_size_target)}")
    print(f"Number of files to transfer from target to source: {len(to_transfer_from_target)}")
    print(f"Number of common files: {len(common_files)}")

    # Check free space
    free_space_after_sync, free_space_percentage = check_free_space(target, total_size)
    print(f"Free space after sync in target: {format_size(free_space_after_sync)} ({free_space_percentage:.2f}%)")

    if free_space_after_sync < 0:
        print("Not enough free space in the target directory to complete the operation.")
        return

    proceed = input("Do you want to proceed with the file operations? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Operation cancelled.")
        return

    # Copy files to transfer from source to target
    for file in tqdm(to_transfer, desc="Transferring files from source to target"):
        target_path = target / file.relative_to(source)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, target_path)

    # Check free space for source before copying files from target to source
    free_space_after_sync_source, free_space_percentage_source = check_free_space(source, total_size_target)
    print(f"Free space after sync in source: {format_size(free_space_after_sync_source)} ({free_space_percentage_source:.2f}%)")

    if free_space_after_sync_source < 0:
        print("Not enough free space in the source directory to complete the operation.")
        return

    # Copy files to transfer from target to source
    for file in tqdm(to_transfer_from_target, desc="Transferring files from target to source"):
        source_path = source / file.relative_to(target)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file, source_path)

    logging.info(f"Sync complete. Total size transferred from source to target: {format_size(total_size)}")
    logging.info(f"Number of files transferred from source to target: {len(to_transfer)}")
    logging.info(f"Sync complete. Total size transferred from target to source: {format_size(total_size_target)}")
    logging.info(f"Number of files transferred from target to source: {len(to_transfer_from_target)}")

if __name__ == "__main__":
    setup_logging()
    source_folder = get_folder_path("Enter the source folder path: ")
    target_folder = get_folder_path("Enter the target folder path: ")

    max_workers = min(32, (multiprocessing.cpu_count() + 4))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        compare_and_sync(source_folder, target_folder, executor)
