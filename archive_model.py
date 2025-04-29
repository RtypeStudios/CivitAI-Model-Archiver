import hashlib
import logging
import urllib.parse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import argparse
import sys
from tqdm import tqdm
import requests

from common.tools import Tools
from models.model import Model
from models.version import Version
from exceptions.failed_hash_check_exception import FailedHashCheckException
from tasks.download import Download
from tasks.write_description import WriteDescription
from tasks.write_metadata import WriteMetadata
from tasks.write_trained_words import WriteTrainedWords

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, f"log-{time.strftime('%Y%m%d%H%M%S')}.log")
MAX_PATH_LENGTH = 200
BASE_URL = "https://civitai.com/api/v1/models"

logger = logging.getLogger('default')
logger.setLevel(logging.DEBUG)
file_handler_md = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler_md.setLevel(logging.DEBUG)
file_handler_md.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler_md)

class Processor:
    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self, output_dir:str, token:str, max_tries:int, retry_delay:int, max_threads:int):
        self.session = requests.Session()
        self.output_dir = Tools.sanitize_directory_name(output_dir)
        self.token = token
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.max_threads = max_threads
        self.work_summary = {}

    # ------------------------------------
    # Main Worker.
    # ------------------------------------

    def archive_user(self, username:str):
        '''
        Exctract all models for a given user.
        '''
        page = f"{BASE_URL}?{urllib.parse.urlencode({ "username": username, "nsfw": "true" })}"

        while True:
            if page is None:
                print("End of pagination reached: 'next_page' is None.")
                break

            user_data_page = Tools.get_json_with_retry(self.session, page, self.token, self.retry_delay)

            for model_data in user_data_page['items']:
                self.build_tasks(username, model_data)

            metadata = user_data_page.get('metadata', {})
            page = metadata.get('nextPage')

            if not metadata and not user_data_page['items']:
                print("Termination condition met: 'metadata' is empty.")
                break


    def archive_model(self, model_id):
        '''
        Extract model data.
        '''
        # Create output directory for model archives
        model_data = Tools.get_json_with_retry(self.session, f"{BASE_URL}/{model_id}?{urllib.parse.urlencode({ "nsfw": "true" })}", self.token, self.retry_delay)

        #print(f"Model data: {json.dumps(model_data, indent=4)}")

        # Add model data to the summary.
        self.build_tasks(model_data['creator']['username'], model_data)


    def build_tasks(self, username:str, model_data: dict[str, object]) -> Model:
        '''
        Do the extraction of model data.
        '''
        username            = Tools.sanitize_name(username, max_length=MAX_PATH_LENGTH)
        model_id            = model_data['id']
        model_name          = Tools.sanitize_name(model_data['name'], max_length=MAX_PATH_LENGTH)
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
                current_version.tasks.append(Download(model_file['name'], version_output_path, model_file['downloadUrl'], model_file['hashes']['SHA256'], model_file['sizeKB']))

            for idx, model_image in enumerate(version['images']):
                file_extension = Tools.get_file_extension_regex(model_image['url'])
                current_version.tasks.append(Download(f'{idx}.{file_extension}', version_output_path, model_image['url']))

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
        print()
        print('Below are a list of the requested tasks (Note: anything already downloaded will be skipped).')
        print()

        for username, models in self.work_summary.items():
            print(f"User: {username}")
            print()
            for m in models:
                print(f"\tModel: {m.name} ({m.id}) type: {m.type})")
                print("\t\tTasks:")
                for t in m.tasks:
                    print(f"\t\t\t{t.name}")
                print()
                for v in m.versions:
                    print(f"\tVersion: {v.id} ({v.name}) based on {v.base_model}")
                    print("\t\tTasks:")
                    for t in v.tasks:
                        print(f"\t\t\t{t.name}")
                print()
            print()
            print()


    def do_work(self):
        '''
        Actually start doing the donwload.
        '''
        print()
        print("Starting work.")
        print(f"Output directory: {self.output_dir}")
        print(f"Max threads: {self.max_threads}")
        print(f"Max tries: {self.max_tries}")
        print(f"Retry delay: {self.retry_delay} seconds")
        print()

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
                    output_path_and_filename = os.path.join(task.output_path, task.file_name)
                    if isinstance(task, Download):
                        futures.append(executor.submit(self.download_file_or_image, task.url, output_path_and_filename, task.sha256_hash))
                    elif isinstance(task, WriteMetadata):
                        futures.append(executor.submit(Tools.write_file, output_path_and_filename, task.metadata))
                    elif isinstance(task, WriteDescription):
                        futures.append(executor.submit(Tools.write_file, output_path_and_filename, task.description))
                    elif isinstance(task, WriteTrainedWords):
                        futures.append(executor.submit(Tools.write_file, output_path_and_filename, task.trained_words))

                for future in as_completed(futures):
                    pbar.update(1)
                    future.result()

                    # Check if the furture raised an exception
                    if future.exception() is not None:
                        print(f"Error: {future.exception()}")


    def verify_hash(self, file_path, expected_hash, existing):
        '''
        Verify the SHA256 hash of a file.
        '''
        sha256 = hashlib.sha256()
        filesize = os.path.getsize(file_path)

        title = "Verifying Download"

        if existing:
            title = 'Verifying existing file'

        progress_bar = tqdm(desc=title, total=filesize, unit='B', unit_scale=True, leave=False, colour='blue')

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                progress_bar.update(len(chunk))
                sha256.update(chunk)

        progress_bar.close()
        result_hash = sha256.hexdigest().upper()
        expected_hash = expected_hash.upper()

        return result_hash == expected_hash


    def download_file_or_image(self, url, output_path, sha256_hash='', retry_count=0, max_retries=3):
        '''
        Download a file or image from the provided URL.
        '''
        progress_bar = None

        try:

            # Check if the file already exists
            if os.path.exists(output_path):
                # return True
                if sha256_hash is not None and sha256_hash != '':
                    # Check if the file Hash matches, if not, continue to download.
                    if self.verify_hash(output_path, sha256_hash, existing=True):
                        return True
                    else:
                        raise FailedHashCheckException("File failed hash check on existing completed file")
                else:
                    # Skip files without hashes.
                    return True

            output_path_tmp = output_path + '.tmp'
            os.makedirs(os.path.dirname(output_path_tmp), exist_ok=True)

            progress_bar = None
            title = "Downloading"
            color = 'YELLOW'
            mode = 'wb'

            if retry_count > 0:
                title = f"Downloading Retry: {retry_count}/{max_retries}"

            headers = {"Authorization": f"Bearer {self.token}"}

            if os.path.exists(output_path_tmp):
                # Resume existing download.
                headers['Range'] = f'bytes={os.path.getsize(output_path_tmp)}-'
                color = 'MAGENTA'
                mode = 'ab'
                title = 'Resumed Download'

            response = self.session.get(url, stream=True, timeout=(20, 40), headers=headers)

            if response.status_code == 404:
                print(f"File not found: {url}")
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
                if self.verify_hash(output_path, sha256_hash, existing=False) is False:
                    raise FailedHashCheckException("File failed hash check after download")
                


        except (FailedHashCheckException) as e:
            logger.exception(f"Hash verification failed for {url} renaming file and redownloading", e)
            os.rename(output_path, output_path + '.failed_hash')
            if retry_count < max_retries:
                time.sleep(self.retry_delay)
                return self.download_file_or_image(url, output_path, sha256_hash, retry_count, max_retries)
        except (requests.RequestException, requests.HTTPError, requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout, requests.exceptions.ChunkedEncodingError) as e:
            logger.exception(f"exception {url}", e)
            if retry_count < max_retries:
                time.sleep(self.retry_delay)
                return self.download_file_or_image(url, output_path, sha256_hash, retry_count + 1, max_retries)
        except (Exception) as e:
            logger.exception(f"general exception occured", e)
        finally:
            if progress_bar:
                progress_bar.close()

        return True



if __name__ == "__main__":

    # Argument parsing.
    parser = argparse.ArgumentParser(description="Download model files and images from Civitai API.")
    parser.add_argument("--usernames", nargs='+', type=str, help="Enter one or more usernames you want to download from.")
    parser.add_argument("--models", nargs='+', type=str, help="Enter one or more models you want to download.")
    parser.add_argument("--retry_delay", type=int, default=10, help="Retry delay in seconds.")
    parser.add_argument("--max_tries", type=int, default=3, help="Maximum number of retries.")
    parser.add_argument("--max_threads", type=int, default=5, help="Maximum number of concurrent threads. Too many produces API Failure.")
    parser.add_argument("--token", type=str, default=None, help="API Token for Civitai.")
    parser.add_argument("--output_dir", type=str, default='model_archives', help="The place to output the downloads, defaults to 'model_archives'.")
    args = parser.parse_args()

    # Validate input arguments.
    if args.token is None:
        args.token = input("Please enter your Civitai API token: ")
        sys.exit(1)

    if args.usernames is None and args.models is None:
        print("Please provide at least one username or model id.")
        sys.exit(1)

    logger.info(f"Starting")

    # Build processor.
    Processor = Processor(args.output_dir, args.token, args.max_tries, args.retry_delay, args.max_threads)

    # Process provided users.
    if args.usernames is not None:
        for u in args.usernames:
            print(f"Processing user: {u}")
            Processor.archive_user(u)

    # Process provided model ids.
    if args.models is not None:
        for mid in args.models:
            print(f"Processing model with id: {mid}")
            Processor.archive_model(mid)

    Processor.summerise()

    while True:
        proceed = input("Do you want to continue? (y/n): ")
        if proceed.lower() == 'n':
            print("Exiting.")
            sys.exit(1)
        elif proceed.lower() == 'y':
            print("Continuing...")
            break

    Processor.do_work()
