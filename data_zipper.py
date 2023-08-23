import glob
import os
import subprocess
import tarfile

from tqdm import tqdm
from tqdm.contrib.concurrent import process_map


def get_file_zipped(target_folder: str, max_size_mb: int):
    """This function will zip all files in the target folder; in the meantime, it will close the zip if it is larger than the max_size_mb.

    Args:
        target_folder (str): The folder name that you want to zip.
        max_size_mb (int, optional): The max size of the zip file. Defaults to 90.

    Return:
        None

    Example:
        target_folder: 藍新金流_20230813
        source_foldername: data/藍新金流_20230813
        foldername: 藍新金流
        filename: 藍新金流_20230813

        path should looks like this:
        data
        ├── 藍新金流
        │   ├── 藍新金流_20230813
        │   │   ├── 藍新金流_20230813_1.tar.gz
        │   │   ├── 藍新金流_20230813_2.tar.gz
    """
    source_foldername = f"data/{target_folder}"
    filename = os.path.basename(source_foldername)
    foldername = filename.split('_')[0]
    subfoldername = filename
    os.makedirs(f"zipped_data/{foldername}/{subfoldername}", exist_ok=True)

    file_number = 1
    output_filename = f"zipped_data/{foldername}/{subfoldername}/{filename}_{file_number}.tar.gz"
    tarf = tarfile.open(output_filename, 'w:gz')

    max_size = max_size_mb * 1024 * 1024
    file_list = glob.glob(f'{source_foldername}/*.png')
    with tqdm(total=len(file_list), desc="Packing files", position=1, leave=False, ascii=True, colour='white', bar_format='{l_bar}{bar}{r_bar}') as pbar:
        for file_name in file_list:
            tarf.add(file_name, arcname=os.path.basename(file_name))
            current_filesize = os.path.getsize(output_filename)
            pbar.set_postfix_str(f"File: {os.path.basename(file_name)} with {round(current_filesize / 1024 / 1024, 2)} Mb", refresh=True)
            pbar.update(1)
            if current_filesize > max_size:
                tarf.close()
                file_number += 1
                output_filename = f"zipped_data/{foldername}/{subfoldername}/{filename}_{file_number}.tar.gz"
                tarf = tarfile.open(output_filename, 'w:gz')

    tarf.close()

def git_push(message: str, push_target: str):
    cmd = ["git", "add", f"{push_target}"]
    subprocess.run(cmd)
    commit_message = f"update datasets for {message}"
    cmd = ["git", "commit", "-m", commit_message]
    subprocess.run(cmd)
    cmd = ["git", "push"]
    subprocess.run(cmd)

def main():
    foldernames = list(os.listdir("data"))
    max_size_mb = 90
    # process_map(get_file_zipped, foldernames, desc="Zipping files")
    with tqdm(total=len(foldernames), desc="Zipping files", position=0, leave=False, ascii=True, colour='green', bar_format='{l_bar}{bar}{r_bar}') as pbar:
        for foldername in foldernames:
            get_file_zipped(foldername, max_size_mb)
            pbar.set_postfix_str(f"Folder: {foldername}", refresh=True)
            pbar.update(1)
            git_push(foldername, f"zipped_data/{foldername}")

if __name__ == "__main__":
    main()
