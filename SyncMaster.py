import os
import shutil
import humanize
import hashlib
from pathlib import Path
import logging
import concurrent.futures
import multiprocessing

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

def file_hash(file_path):
    hasher = hashlib.sha256()
    with file_path.open('rb') as f:
        for buf in iter(lambda: f.read(4096), b''):
            hasher.update(buf)
    return hasher.hexdigest()

def compare_and_sync(source, target, executor):
    source_files = get_all_files(source)
    target_files = get_all_files(target)

    target_files_dict = {file.relative_to(target): file for file in target_files}
    target_hashes = {rel_path: executor.submit(file_hash, file) for rel_path, file in target_files_dict.items()}

    common_files = set()
    to_transfer = []
    total_size = 0

    future_to_file = {executor.submit(file_hash, src_file): src_file for src_file in source_files}

    processed_files = 0
    for future in concurrent.futures.as_completed(future_to_file):
        src_file = future_to_file[future]
        relative_path = src_file.relative_to(source)
        try:
            src_hash = future.result()
            tgt_file = target_files_dict.get(relative_path)
            if tgt_file and src_hash == target_hashes[relative_path].result():
                common_files.add(relative_path)
            else:
                to_transfer.append(src_file)
                total_size += src_file.stat().st_size
        except Exception as e:
            logging.error(f"Error processing {src_file}: {e}")

        processed_files += 1
        if processed_files % 10 == 0:  # Log every 10 files processed
            logging.info(f"Processed {processed_files} files...")

    for tgt_file in target_files:
        relative_path = tgt_file.relative_to(target)
        if relative_path not in common_files and relative_path not in (file.relative_to(source) for file in source_files):
            to_transfer.append(tgt_file)
            total_size += tgt_file.stat().st_size

    return common_files, to_transfer, total_size

def copy_file(src_file, target_path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_file, target_path)

def check_free_space(target, total_size):
    stat = shutil.disk_usage(target)
    free_space_after_sync = stat.free - total_size
    free_space_percentage = (free_space_after_sync / stat.total) * 100
    return free_space_after_sync, free_space_percentage

def sync_folders(source, target):
    num_cores = multiprocessing.cpu_count()
    num_threads = max(1, num_cores * 2 // 3)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        common_files, to_transfer, total_size = compare_and_sync(source, target, executor)

        logging.info(f"Similarity: {len(common_files)} files are common in both folders.")
        logging.info(f"Files to be transferred: {len(to_transfer)}")
        logging.info(f"Total file size to be transferred: {humanize.naturalsize(total_size, binary=True)}")

        free_space_after_sync, free_space_percentage = check_free_space(target, total_size)
        if free_space_percentage < 15:
            logging.warning(f"Warning: Free space after syncing will be less than 15%. Estimated free space: {free_space_percentage:.2f}%")
            logging.info(f"Total free space after syncing: {humanize.naturalsize(free_space_after_sync, binary=True)}")
        
        proceed = input("Do you want to proceed with the synchronization? (y/n): ").strip().lower()
        if proceed == 'y':
            future_to_file = {}
            processed_files = 0
            for file in to_transfer:
                if file.is_relative_to(source):
                    relative_path = file.relative_to(source)
                    target_path = target / relative_path
                else:
                    relative_path = file.relative_to(target)
                    target_path = source / relative_path

                future_to_file[executor.submit(copy_file, file, target_path)] = file

                processed_files += 1
                if processed_files % 10 == 0:  # Log every 10 files processed
                    logging.info(f"Copied {processed_files} files...")

            for future in concurrent.futures.as_completed(future_to_file):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error copying file: {e}")

            logging.info("Synchronization complete.")
        else:
            logging.info("Synchronization aborted.")

if __name__ == "__main__":
    setup_logging()
    
    source_folder = get_folder_path("Enter the first folder path: ")
    target_folder = get_folder_path("Enter the second folder path: ")

    sync_folders(source_folder, target_folder)
