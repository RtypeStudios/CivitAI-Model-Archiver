import logging
import urllib.parse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import requests

from common.tools import Tools
from models.model import Model
from models.version import Version
from tasks.download_file import DownloadFile
from tasks.write_description import WriteDescription
from tasks.write_metadata import WriteMetadata
from tasks.write_trained_words import WriteTrainedWords


class Processor:

    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self, output_dir:str, token:str, max_tries:int, retry_delay:int, max_threads:int, skip_existing_verification:bool):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.session = requests.Session()
        self.output_dir = Tools.sanitize_directory_name(output_dir)
        self.token = token
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.max_threads = max_threads
        self.skip_existing_verification = skip_existing_verification
        self.work_summary = {}

        self.base_url = "https://civitai.com/api/v1/models"
        self.max_path_length = 200

        self.logger.info("Processor initialized with output_dir: %s, max_tries: %d, retry_delay: %d, max_threads: %d, Skip existing verification: %s", self.output_dir, self.max_tries, self.retry_delay, self.max_threads, self.skip_existing_verification)

    # ------------------------------------
    # Main Worker.
    # ------------------------------------

    def archive_user(self, username:str):
        '''
        Exctract all models for a given user.
        '''
        page = f"{self.base_url}?{urllib.parse.urlencode({ "username": username, "nsfw": "true" })}"

        while True:
            if page is None:
                self.logger.info("End of pagination reached: 'next_page' is None.")
                break

            user_data_page = Tools.get_json_with_retry(self.session, page, self.token, self.retry_delay)

            for model_data in user_data_page['items']:
                self.build_tasks(username, model_data)

            metadata = user_data_page.get('metadata', {})
            page = metadata.get('nextPage')

            if not metadata and not user_data_page['items']:
                self.logger.warning("Termination condition met: 'metadata' is empty.")
                break


    def archive_model(self, model_id):
        '''
        Extract model data.
        '''
        # Create output directory for model archives
        model_data = Tools.get_json_with_retry(self.session, f"{self.base_url}/{model_id}?{urllib.parse.urlencode({ "nsfw": "true" })}", self.token, self.retry_delay)

        # Add model data to the summary.
        self.build_tasks(model_data['creator']['username'], model_data)


    def build_tasks(self, username:str, model_data: dict[str, object]) -> Model:
        '''
        Do the extraction of model data.
        '''
        username            = Tools.sanitize_name(username, max_length=self.max_path_length)
        model_id            = model_data['id']
        model_name          = Tools.sanitize_name(model_data['name'], max_length=self.max_path_length)
        model_type          = model_data['type']
        current_model       = Model(model_id, model_name, model_type, model_data['description'])
        model_ouput_path    = os.path.join(self.output_dir, username, f'{model_name} ({model_type})')

        current_model.tasks.append(WriteMetadata(f'{model_id}.json', model_ouput_path, model_data))
        current_model.tasks.append(WriteDescription(model_ouput_path, model_data['description']))

        # Loop through the model versions.
        for version in model_data['modelVersions']:

            # Get fields from model version data
            version_base_model      = version['baseModel'] if version['baseModel'] else ''
            current_version         = Version(model_id, version['name'], version_base_model)
            version_output_path     = os.path.join(model_ouput_path, f'{version["name"]} ({version_base_model})')

            current_version.tasks.append(WriteTrainedWords(version_output_path, version.get('trainedWords', [])))

            for model_file in version['files']:
                current_version.tasks.append(DownloadFile(self.token, 
                                                          model_file['name'], 
                                                          version_output_path, 
                                                          model_file['downloadUrl'], 
                                                          model_file['hashes']['SHA256'], 
                                                          model_file['sizeKB'], 
                                                          rety_delay=self.retry_delay, 
                                                          skip_existing_verification=self.skip_existing_verification))

            for idx, model_image in enumerate(version['images']):
                file_extension = Tools.get_file_extension_regex(model_image['url'])
                current_version.tasks.append(DownloadFile(self.token, 
                                                          f'{idx}.{file_extension}', 
                                                          version_output_path, 
                                                          model_image['url'], 
                                                          rety_delay=self.retry_delay, 
                                                          skip_existing_verification=self.skip_existing_verification))

            current_model.versions.append(current_version)

        self.add_to_download_summary(username, current_model)


    def add_to_download_summary(self, username: str, model: Model):
        '''
        Helper method to init the models to and empty array before adding one.
        '''
        if username not in self.work_summary:
            self.work_summary[username] = []

        self.work_summary[username].append(model)


    def summerise(self):
        '''
        Write the summary information for the user.
        '''

        summary = 'Below are a list of the requested tasks (Note: anything already downloaded will be skipped).'
        summary += os.linesep

        for username, models in self.work_summary.items():
            summary += f"User: {username}" + os.linesep
            summary += os.linesep
            for m in models:
                summary += f"\tModel: {m.name} ({m.id}) type: {m.type})" + os.linesep
                summary += "\t\tTasks:" + os.linesep
                for t in m.tasks:
                    summary += f"\t\t\t{t.name}" + os.linesep
                summary += os.linesep
                for v in m.versions:
                    summary += f"\tVersion: {v.id} ({v.name}) based on {v.base_model}" + os.linesep
                    summary += "\t\tTasks:" + os.linesep
                    for t in v.tasks:
                        summary += f"\t\t\t{t.name}" + os.linesep
                    summary += os.linesep
                summary += os.linesep

        self.logger.info(summary)



    def do_work(self):
        '''
        Actually start doing the donwload.
        '''
        self.logger.info("Starting work.")
        self.logger.info("Output directory: %s", self.output_dir)
        self.logger.info("Max threads: %s", self.max_threads)
        self.logger.info("Max tries: %s", self.max_tries)
        self.logger.info("Retry delay: %s seconds", self.retry_delay)

        tasks = []

        for _, models in self.work_summary.items():
            for m in models:
                for t in m.tasks:
                    tasks.append(t)
                for v in m.versions:
                    for t in v.tasks:
                        tasks.append(t)

        with tqdm(total=len(tasks), desc="Procesing Tasks", unit="task", colour='green') as pbar:
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []

                for task in tasks:
                    futures.append(executor.submit(task.run))

                for future in as_completed(futures):
                    pbar.update(1)
                    future.result()

                    # Check if the furture raised an exception
                    if future.exception() is not None:
                        e = future.exception()
                        logging.error("%s error occurred: %s", type(e), e, stack_info=True, exc_info=True)


    # def verify_hash(self, file_path, expected_hash):
    #     '''
    #     Verify the SHA256 hash of a file.
    #     '''
    #     sha256 = hashlib.sha256()
    #     filesize = os.path.getsize(file_path)

    #     progress_bar = tqdm(desc="Verifying Download", total=filesize, unit='B', unit_scale=True, leave=False, colour='blue')

    #     with open(file_path, "rb") as f:
    #         for chunk in iter(lambda: f.read(4096), b""):
    #             progress_bar.update(len(chunk))
    #             sha256.update(chunk)

    #     progress_bar.close()
    #     result_hash = sha256.hexdigest().upper()
    #     expected_hash = expected_hash.upper()

    #     return result_hash == expected_hash


    # def download_file_or_image(self, url, output_path, sha256_hash='', retry_count=0, max_retries=3):
    #     '''
    #     Download a file or image from the provided URL.
    #     '''
    #     progress_bar = None

    #     try:

    #         # Check if the file already exists
    #         if os.path.exists(output_path):
    #             # Are we verifying a existing files?
    #             if self.skip_existing_verification is False:
    #                 # Do we have a hash to check against?
    #                 if sha256_hash is not None and sha256_hash != '':
    #                     # Check if the file Hash matches, if not, continue to download.
    #                     if self.verify_hash(output_path, sha256_hash):
    #                         # If it does retorn
    #                         return True
    #                     else:
    #                         # Throw an error if the existing haah is bad and handle it in the exception block.
    #                         raise FailedHashCheckException("File failed hash check on existing completed file")
    #                 else:
    #                     # Skip files without hashes.
    #                     return True
    #             else:
    #                 # Skip verification.
    #                 return True

    #         output_path_tmp = output_path + '.tmp'
    #         os.makedirs(os.path.dirname(output_path_tmp), exist_ok=True)

    #         progress_bar = None
    #         title = "Downloading"
    #         color = 'YELLOW'
    #         mode = 'wb'

    #         if retry_count > 0:
    #             title = f"Downloading Retry: {retry_count}/{max_retries}"
    #             self.logger.warning("Downloading Retry for: %s %s %s", url,retry_count, max_retries)

    #         headers = {"Authorization": f"Bearer {self.token}"}

    #         if os.path.exists(output_path_tmp):
    #             # Resuming existing download.
    #             headers['Range'] = f'bytes={os.path.getsize(output_path_tmp)}-'
    #             color = 'MAGENTA'
    #             mode = 'ab'
    #             title = 'Resumed Download'

    #         response = self.session.get(url, stream=True, timeout=(20, 40), headers=headers)

    #         if response.status_code == 404:
    #             self.logger.warning("File not found: %s", url)
    #             return False

    #         if response.status_code == 416:
    #             self.logger.warning(f"could not resume download, resume was: %s %s", headers['Range'], url)
    #             return False

    #         response.raise_for_status()

    #         total_size = int(response.headers.get('content-length', 0))

    #         progress_bar = tqdm(desc=title, total=total_size, unit='B', unit_scale=True, leave=False, colour=color)

    #         with open(output_path_tmp, mode) as file:
    #             for chunk in response.iter_content(chunk_size=8192):
    #                 if chunk:
    #                     progress_bar.update(len(chunk))
    #                     file.write(chunk)

    #         progress_bar.close()

    #         os.rename(output_path_tmp, output_path)

    #         if sha256_hash is not None and sha256_hash != '':
    #             if self.verify_hash(output_path, sha256_hash) is False:
    #                 raise FailedHashCheckException("File failed hash check after download")

    #         return True

    #     except (FailedHashCheckException) as e:
    #         if retry_count < max_retries:
    #             os.rename(output_path, output_path + f'.failed_hash{retry_count}')
    #             time.sleep(self.retry_delay)
    #             return self.download_file_or_image(url, output_path, sha256_hash, retry_count, max_retries)
    #         else:
    #             self.logger.exception("Hash verification failed for %s renaming file and re-downloading", url, exc_info=e)
    #             return False

    #     except (requests.RequestException, requests.HTTPError, requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout, requests.exceptions.ChunkedEncodingError, urllib3.exceptions.ProtocolError, urllib3.exceptions.IncompleteRead) as e:
    #         if retry_count < max_retries:
    #             time.sleep(self.retry_delay)
    #             return self.download_file_or_image(url, output_path, sha256_hash, retry_count + 1, max_retries)
    #         else:
    #             self.logger.exception("exception %s", url, exc_info=e)
    #             return False

    #     finally:
    #         if progress_bar:
    #             progress_bar.close()
