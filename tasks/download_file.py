import hashlib
import os
import sys
import time

import py7zr
import requests
from tqdm import tqdm

from tasks.task import Task

class DownloadFile(Task):
    '''
    Download a file from a given URL and save it to the specified output path.
    '''
    def __init__(self, token:str, file_name:str, output_path:str, url:str, retry_delay, max_retry,  sha256_hash='', file_size=0, skip_existing_verification=False, compress=False):
        super().__init__(f'Download File: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.token = token
        self.url = url
        self.sha256_hash = sha256_hash
        self.file_size = file_size
        self.retry_delay = retry_delay
        self.max_retry = max_retry
        self.skip_existing_verification = skip_existing_verification
        self.output_path_and_filename = os.path.join(self.output_path, self.file_name)
        self.compress = compress

    def run(self):
        '''
        Download a file or image from the provided URL.
        '''
        self.logger.debug('Downloading Data: %s to %s', self.url, self.output_path_and_filename)
        
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        temp_output_path        = f'{self.output_path_and_filename}.tmp'
        compressed_output_path  = f'{self.output_path_and_filename}.7z'
        downloaded_output_path  = self.output_path_and_filename

        if os.path.exists(downloaded_output_path) and os.path.exists(compressed_output_path):
            self.logger.debug('Downloaded file and compressed file both exist, assuming application interupted between download and compression phases, removing compressed: %s %s', downloaded_output_path, compressed_output_path)
            os.remove(compressed_output_path)

        # Check the file exists compressed
        if self.compress and os.path.exists(compressed_output_path):
            self.logger.debug('Compressed File already exists: %s', compressed_output_path)
            return

        # Check the file exists uncompressed
        elif os.path.exists(downloaded_output_path):

            # Are we checking existing hashes and if so, do we have an SHA256? If so check the file
            if (self.skip_existing_verification is not True and
                self.sha256_hash is not None and
                self.sha256_hash != ''):

                # Does the file verify?
                if self.verify(downloaded_output_path, self.sha256_hash) is not True:

                    # Remove the existing file and recurse.
                    os.rename(downloaded_output_path, downloaded_output_path + f'.failed_hash_{time.strftime('%Y%m%d%H%M%S')}')
                    return self.run()
            
            # compression enabled?
            if self.compress:
                # compress the file
                self.compress_and_remove(downloaded_output_path, compressed_output_path)

            # All good return.
            return
            
        else:

            # Download the file
            self.download(self.url, temp_output_path, downloaded_output_path)

            # Check this file exists
            if os.path.exists(downloaded_output_path):

                # Verify the file
                if self.sha256_hash is not None and self.sha256_hash != '':
                    if self.verify(downloaded_output_path, self.sha256_hash) is not True:
                        # Remove the existing file and recurse.
                        os.rename(downloaded_output_path, downloaded_output_path + f'.failed_hash_{time.strftime('%Y%m%d%H%M%S')}')
                        return self.run()

                # compression enabled?
                if self.compress:
                    # compress the file
                    self.compress_and_remove(downloaded_output_path, compressed_output_path)

            else:
                self.logger.error("Downloaded file not found? %s", downloaded_output_path)

            return


    def download(self, url, temp_output_path, output_path):
        '''
        Download a file from a given URL and save it to the specified output path.
        '''
        # Resume download to temp file.
        self.logger.debug('Downloading: %s to %s, Resuming? %s', url, output_path, os.path.exists(temp_output_path))

        for r in range(self.max_retry):

            try:
                action = f'Downloading, Attempt: {r+1}/{self.max_retry}'

                # Check if the file already exists
                if os.path.exists(temp_output_path):
                    self.logger.debug('Resuming download: %s', temp_output_path)
                    resume_header = {'Range': f'bytes={os.path.getsize(temp_output_path)}-'}
                    color = 'MAGENTA'
                    action = f'Resumed Download, Attempt: {r+1}/{self.max_retry}'
                else:
                    resume_header = {}
                    color = 'YELLOW'

                # Download the file with progress bar
                with requests.get(url, headers={ 'Authorization': f'Bearer {self.token}', **resume_header }, stream=True, timeout=2000, allow_redirects=True) as response:

                    if response.status_code == 401:
                        self.logger.debug("Unauthorized for url (Model Removed?): %s", url)
                        return False

                    if response.status_code == 404:
                        self.logger.debug("File not found: %s", url)
                        return False

                    if response.status_code == 416:
                        self.logger.debug("Could not resume download, resume was: (%s/%s) %s -> %s", resume_header['Range'], int(response.headers.get('Content-Length', 0)), url, temp_output_path)
                        return False

                    response.raise_for_status()

                    with tqdm(desc=action,
                              total=int(response.headers.get('Content-Length', 0)),
                              unit='B',
                              unit_scale=True,
                              colour=color, 
                              leave=False) as progres_bar:

                        with open(temp_output_path, 'ab') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                                progres_bar.update(len(chunk))

                # Rename the temp file to the final output path
                self.logger.debug("Download complete, renaming %s -> %s", temp_output_path, output_path)
                os.rename(temp_output_path, output_path)

                # Break out of retry loop if download was successful
                return True

            except (requests.exceptions.RequestException, requests.HTTPError, requests.ConnectionError, requests.Timeout) as e:
                self.logger.error("Error downloading file: %s", e)
                time.sleep(self.retry_delay)

            except (Exception) as e:
                self.logger.error("Error Occured", e)


        self.logger.error("Failed to download file: %s, hit max retries.", url)


    def verify(self, output_path, expected_hash):
        '''
        Verify the SHA256 hash of a file.
        '''
        sha256 = hashlib.sha256()
        filesize = os.path.getsize(output_path)
        progress_bar = tqdm(desc="Verifying Download", total=filesize, unit='B', unit_scale=True, leave=False, colour='blue')

        with open(output_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                progress_bar.update(len(chunk))
                sha256.update(chunk)

        progress_bar.close()

        return sha256.hexdigest().upper() == expected_hash.upper()


    def compress_and_remove(self, input_path, output_path):
        '''
        Compress a file using 7zip.
        '''
        self.logger.debug("Compressing %s to %s", input_path, output_path)

        progress_bar = tqdm(desc="Compressing Download", total=1, unit='B', unit_scale=True, leave=False, colour='blue')

        # Stream to provide useful progres report? https://gist.github.com/reimarstier/8aa6822045dc6b562beea44799f94061
        with py7zr.SevenZipFile(output_path, 'w', filters=[{"id": py7zr.FILTER_LZMA2, "preset": 8}]) as archive:
            archive.write(input_path, self.file_name)
            progress_bar.update(1)

        # Testing seems to return none becuase CRC is missing?
        # with py7zr.SevenZipFile(output_path, 'r') as archive:
        #     result = archive.testzip()
        #     print(result)
        #     progress_bar.update(2)

        progress_bar.close()

        self.logger.debug("Compressing successful, removing %s", input_path)
        os.remove(input_path)
