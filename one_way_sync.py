import os
import hashlib
import shutil
import logging

def blake2_hash(file_path):
    BUF_SIZE = 65536  # read stuff in 64kb chunks
    blake2 = hashlib.blake2b()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            blake2.update(data)
    return blake2.hexdigest()

def one_way_sync(folder_a, folder_b):
    if not os.path.exists(folder_b):
        os.makedirs(folder_b)

    copied_files_count = 0
    total_copied_size = 0

    for root, dirs, files in os.walk(folder_a):
        for file in files:
            file_a = os.path.join(root, file)
            relative_path = os.path.relpath(file_a, folder_a)
            file_b = os.path.join(folder_b, relative_path)

            if not os.path.exists(file_b) or blake2_hash(file_a) != blake2_hash(file_b):
                if not os.path.exists(os.path.dirname(file_b)):
                    os.makedirs(os.path.dirname(file_b))
                shutil.copy2(file_a, file_b)
                copied_files_count += 1
                total_copied_size += os.path.getsize(file_a)

    total_copied_size_gib = total_copied_size / (1024 ** 3)
    logging.info(f"Total files copied: {copied_files_count}")
    logging.info(f"Total copied file size: {total_copied_size_gib:.4f} GiB")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    folder_a = input("Enter the source folder (A): ")
    folder_b = input("Enter the destination folder (B): ")
    one_way_sync(folder_a, folder_b)
