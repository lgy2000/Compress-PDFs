#!/usr/bin/env python3

"""
compress.py

This module is used for compressing PDF files.

Description:
This module uses the iLovePDF API to compress PDF files. It reads the public keys from a configuration file, asks the user to select a PDF file or
a folder containing PDF files, and then compresses the selected file(s) using the iLovePDF API. The compressed file(s) are saved with a specific
naming pattern.
"""

import configparser
import glob
import os
import re
import shutil
import sys
import time
import zipfile
from fnmatch import fnmatch
from pathlib import Path

from pylovepdf.ilovepdf import ILovePdf

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
all_pdfs_pattern = "*.pdf"
compressed_pdfs_pattern = "*compress*.pdf"
compressed_zip_pattern = "*compress*.zip"
compressed_file_regex_pattern = "_compress_\d\d\-\d\d\-\d\d\d\d"
pdf_files = []
compressed_pdfs = []
output_errors = ""

# obtain public key from the .env file
config = configparser.ConfigParser()
config.read(BASE_DIR + '/.env')
public_key1 = config['ILOVEPDF_USER_INFO']['PUBLIC_KEY1']
public_key2 = config['ILOVEPDF_USER_INFO']['PUBLIC_KEY2']
public_key3 = config['ILOVEPDF_USER_INFO']['PUBLIC_KEY3']

# path found as first argument
if len(sys.argv) > 1 and os.path.exists(Path(sys.argv[1]).resolve()):
    action_path = sys.argv[1]
else:  # path not found or not defined (use the current working directory)
    action_path = os.getcwd()

for path, subdirs, files in os.walk(action_path):  # find all the pdfs
    for name in files:
        if fnmatch(name, all_pdfs_pattern):
            pdf_files.append(os.path.join(path, name))

ilovepdf = ILovePdf(public_key, verify_ssl=True)
task = ilovepdf.new_task('compress')

for file in pdf_files:  # upload all the pdfs
    print("Uploading: " + file)
    task.add_file(file)
    task.set_output_folder(action_path)
    task.file.set_metas('Title', file)
task.execute()
task.download()
task.delete_current_task()

time.sleep(3)  # wait for the task to finish

# unzip the downloaded compressed pdf files
zip_file_location = glob.glob(action_path + "/" + compressed_zip_pattern)[0]
with zipfile.ZipFile(zip_file_location, 'r') as zip_ref:
    zip_ref.extractall(action_path)
time.sleep(3)
compressed_pdfs = glob.glob(os.path.join(action_path, compressed_pdfs_pattern))

# replace the recently compressed files to their original file location
for original_file in pdf_files:
    for compressed in compressed_pdfs:
        compressed_file = re.sub(
            compressed_file_regex_pattern, '', compressed)
        if compressed_file[compressed_file.rindex("/")::] in original_file:
            if os.path.exists(Path(original_file).resolve()) and os.path.exists(Path(compressed).resolve()):
                print("Replacing " + compressed + " to " + original_file)
                shutil.move(Path(compressed), Path(original_file))
            else:  # file couldn't be replaced
                output_errors += "\n\033[1;31;40mError:\033[0m Couldn't replace: " + \
                                 compressed + " to " + original_file + '\n'

# show all errors all together
if len(output_errors) > 0:
    print(
        "\n\033[91mFILES THAT COULDN'T BE REPLACED AND THEY MANUALLY HAVE TO BE REPLACED\033[0m")
    print(output_errors)

# delete zip file
os.remove(zip_file_location)
