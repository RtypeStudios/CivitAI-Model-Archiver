import hashlib
import os
import time

import requests
from tqdm import tqdm
import urllib3
from exceptions.failed_hash_check_exception import FailedHashCheckException
from tasks.task import Task

class DownloadFile(Task):
    '''
    Download a file from a given URL and save it to the specified output path.
    '''
    def __init__(self, token:str, file_name:str, output_path:str, url:str, sha256_hash='', file_size=0, retry_delay=10, skip_existing_verification=False):
        super().__init__(f'Download File: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)

        self.token = token
        self.url = url
        self.sha256_hash = sha256_hash
        self.file_size = file_size
        self.retry_delay = retry_delay
        self.skip_existing_verification = skip_existing_verification
        self.output_path_and_filename = os.path.join(self.output_path, self.file_name)

    def run(self):
        '''
        Download a file or image from the provided URL.
        '''
        self.logger.debug('Downloading Data: %s to %s', self.url, self.output_path_and_filename)
        return self.download_file_or_image(self.url, self.output_path_and_filename, self.sha256_hash, 0, 3)


    def download_file_or_image(self, url, output_path, sha256_hash='', retry_count=0, max_retries=3):
        '''
        Download a file or image from the provided URL.
        '''
        progress_bar = None

        try:

            # Check if the file already exists
            if os.path.exists(output_path):

                # Are we verifying a existing files?
                if self.skip_existing_verification is not True:
                    self.logger.debug('Starting verification of existing download: %s', self.output_path_and_filename)

                    if sha256_hash is not None and sha256_hash != '':
                        # Check if the file Hash matches, if not, continue to download.
                        if self.verify_hash(output_path, sha256_hash):
                            self.logger.debug('Validated successfully: %s', self.output_path_and_filename)
                            return True
                        else:
                            # Throw an error if the existing haah is bad and handle it in the exception block.
                            raise FailedHashCheckException("File failed hash check on existing completed file")
                    else:
                        self.logger.debug('No hash found for %s', self.output_path_and_filename)
                        return True
                else:
                    self.logger.debug('Skipping verification of existing download: %s', self.output_path_and_filename)

                return True


            output_path_tmp = output_path + '.tmp'
            os.makedirs(os.path.dirname(output_path_tmp), exist_ok=True)

            progress_bar = None
            title = "Downloading"
            color = 'YELLOW'
            mode = 'wb'

            if retry_count > 0:
                title = f"Downloading Retry: {retry_count}/{max_retries}"
                self.logger.debug("Downloading Retry for: %s %s %s", url,retry_count, max_retries)

            headers = {"Authorization": f"Bearer {self.token}"}

            if os.path.exists(output_path_tmp):
                # Resuming existing download.
                headers['Range'] = f'bytes={os.path.getsize(output_path_tmp)}-'
                color = 'MAGENTA'
                mode = 'ab'
                title = 'Resumed Download'

            response = requests.get(url, stream=True, timeout=(20, 40), headers=headers)

            if response.status_code == 404:
                self.logger.debug("File not found: %s", url)
                return False

            if response.status_code == 416:
                self.logger.debug("could not resume download, resume was: %s %s", headers['Range'], url)
                return False

            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            progress_bar = tqdm(desc=title, total=total_size, unit='B', unit_scale=True, leave=False, colour=color)

            with open(output_path_tmp, mode) as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        progress_bar.update(len(chunk))
                        file.write(chunk)

            progress_bar.close()

            os.rename(output_path_tmp, output_path)

            if sha256_hash is not None and sha256_hash != '':
                if self.verify_hash(output_path, sha256_hash) is False:
                    raise FailedHashCheckException("File failed hash check after download")

            return True

        except (FailedHashCheckException) as e:
            if retry_count < max_retries:
                os.rename(output_path, output_path + f'.failed_hash{retry_count}')
                time.sleep(self.retry_delay)
                return self.download_file_or_image(url, output_path, sha256_hash, retry_count, max_retries)
            else:
                self.logger.exception("Hash verification failed for %s renaming file and re-downloading", url, exc_info=e)
                return False

        except (requests.RequestException, requests.HTTPError, requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout, requests.exceptions.ChunkedEncodingError, urllib3.exceptions.ProtocolError, urllib3.exceptions.IncompleteRead) as e:
            if retry_count < max_retries:
                time.sleep(self.retry_delay)
                return self.download_file_or_image(url, output_path, sha256_hash, retry_count + 1, max_retries)
            else:
                self.logger.exception("exception %s", url, exc_info=e)
                return False

        finally:
            if progress_bar:
                progress_bar.close()



    def verify_hash(self, file_path, expected_hash):
        '''
        Verify the SHA256 hash of a file.
        '''
        sha256 = hashlib.sha256()
        filesize = os.path.getsize(file_path)

        progress_bar = tqdm(desc="Verifying Download", total=filesize, unit='B', unit_scale=True, leave=False, colour='blue')

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                progress_bar.update(len(chunk))
                sha256.update(chunk)

        progress_bar.close()

        result_hash = sha256.hexdigest().upper()
        expected_hash = expected_hash.upper()

        return result_hash == expected_hash
