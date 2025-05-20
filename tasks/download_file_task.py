import os
from pathlib import Path
import time

import requests
from tqdm import tqdm

from common.base_task import BaseTask

class DownloadFileTask(BaseTask):
    '''
    Download a file from a given URL and save it to the specified output path.
    '''
    def __init__(self, url:str, temp_output_path_and_file_name:str, output_path_and_file_name:str, token:str, retry_delay, max_retry, file_size=0):
        self.url = url
        self.output_path_and_file_name = output_path_and_file_name
        self.temp_output_path_and_file_name  = temp_output_path_and_file_name
        self.token = token
        self.file_size = file_size
        self.retry_delay = retry_delay
        self.max_retry = max_retry

        if os.path.exists(self.temp_output_path_and_file_name):
            super().__init__(f'Resume Download File From: \"{url}\" to: \"{Path(temp_output_path_and_file_name).name}\" when complete move to \"{Path(output_path_and_file_name).name}\"')
        else:
            super().__init__(f'Download File: \"{url}\" to: \"{Path(temp_output_path_and_file_name).name}\" when complete move to \"{Path(output_path_and_file_name).name}\"')


    def run(self):
        self.logger.debug('Downloading: %s to %s, Resuming? %s', self.url, self.output_path_and_file_name, os.path.exists(self.temp_output_path_and_file_name))

        for r in range(self.max_retry):
            try:
                action = f'Downloading, Attempt: {r+1}/{self.max_retry}'

                # Check if the file already exists
                if os.path.exists(self.temp_output_path_and_file_name):
                    self.logger.debug('Resuming download: %s', self.temp_output_path_and_file_name)
                    resume_header = {'Range': f'bytes={os.path.getsize(self.temp_output_path_and_file_name)}-'}
                    color = 'MAGENTA'
                    action = f'Resumed Download, Attempt: {r+1}/{self.max_retry}'
                else:
                    resume_header = {}
                    color = 'YELLOW'

                # Download the file with progress bar
                with requests.get(self.url, headers={ 'Authorization': f'Bearer {self.token}', **resume_header }, stream=True, timeout=2000, allow_redirects=True) as response:

                    if response.status_code == 401:
                        self.logger.debug("Unauthorized for url (Model Removed?): %s, Reason: %s", self.url, response.reason)
                        return False

                    if response.status_code == 404:
                        self.logger.debug("File not found (Model Removed?): %s, Reason: %s", self.url, response.reason)
                        return False

                    if response.status_code == 416:
                        self.logger.debug("Exceeded original file size for resume? removing file and starting again. resume was: range: %s, Reason: %s", resume_header['Range'], self.url)
                        if os.path.exists(self.temp_output_path_and_file_name):
                            os.remove(self.temp_output_path_and_file_name)

                    # Anything else raise as an error.
                    response.raise_for_status()

                    with tqdm(desc=action,
                              total=int(response.headers.get('Content-Length', 0)),
                              unit='B',
                              unit_scale=True,
                              colour=color, 
                              leave=False) as progres_bar:

                        with open(self.temp_output_path_and_file_name, 'ab') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                                progres_bar.update(len(chunk))

                # Rename the temp file to the final output path
                self.logger.debug("Download complete, renaming %s -> %s", self.temp_output_path_and_file_name, self.output_path_and_file_name)

                if os.path.exists(self.temp_output_path_and_file_name):
                    os.rename(self.temp_output_path_and_file_name, self.output_path_and_file_name)
                else:
                    self.logger.error("Downloaded file not found? %s", self.temp_output_path_and_file_name)
                    return False

                # Break out of retry loop if download was successful
                return True

            except (requests.exceptions.RequestException, requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
                self.logger.debug("Error downloading file: %s", e)
                time.sleep(self.retry_delay)

            except (Exception) as e:
                self.logger.error("Abnormal Error Occured downloading: %s", self.output_path_and_file_name, type(e), e, stack_info=True, exc_info=True)
                return False

        self.logger.error("Failed to download file: %s, hit max retries.", self.url)
        return False