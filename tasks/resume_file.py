import hashlib
import os
import sys
import time

import py7zr
import requests
from tqdm import tqdm

from tasks.download_file import DownloadFile
from tasks.task import Task

class ResumeFile(DownloadFile):
    '''
    Download a file from a given URL and save it to the specified output path.
    '''
    def __init__(self, token:str, file_name:str, output_path:str, url:str, retry_delay, max_retry,  sha256_hash='', file_size=0, skip_existing_verification=False, compress=False):
        super().__init__(token, file_name, output_path, url, retry_delay, max_retry, sha256_hash, file_size, skip_existing_verification, compress)

    def run(self):
        '''
        Download a file or image from the provided URL.
        '''
        super().run()
