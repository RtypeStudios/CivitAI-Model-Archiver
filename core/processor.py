import logging
import urllib.parse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from common.tools import Tools
from core.metadata_extractor import MetadataExtractor
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
    def __init__(self, output_dir:str, token:str, max_tries:int, retry_delay:int, max_threads:int, skip_existing_verification:bool, only_base_models:list[str], metadata_extractor:MetadataExtractor):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.output_dir = Tools.sanitize_directory_name(output_dir)
        self.token = token
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.max_threads = max_threads
        self.skip_existing_verification = skip_existing_verification
        self.only_base_models = [s.upper() for s in only_base_models]
        self.metadata_extractor = metadata_extractor

        self.work_summary = {}
        self.base_url = "https://civitai.com/api/v1/models"
        self.max_path_length = 200

        self.logger.info("Processor initialized with output_dir: %s, max_tries: %d, retry_delay: %d, max_threads: %d, Skip existing verification: %s", self.output_dir, self.max_tries, self.retry_delay, self.max_threads, self.skip_existing_verification)

        if self.only_base_models is not None:
            self.logger.info("Only fetching models versions based on %s.", "".join(self.only_base_models))


    # # ------------------------------------
    # # Main Worker.
    # # ------------------------------------

    # def archive_user(self, username:str):
    #     '''
    #     Exctract all models for a given user.
    #     '''
    #     page = f"{self.base_url}?{urllib.parse.urlencode({ "username": username, "nsfw": "true" })}"

    #     while True:
    #         if page is None:
    #             self.logger.info("End of pagination reached: 'next_page' is None.")
    #             break

    #         user_data_page = Tools.get_json_with_retry(page, self.token, self.retry_delay)

    #         for model_data in user_data_page['items']:
    #             self.build_tasks(username, model_data)

    #         metadata = user_data_page.get('metadata', {})
    #         page = metadata.get('nextPage')

    #         if not metadata and not user_data_page['items']:
    #             self.logger.warning("Termination condition met: 'metadata' is empty.")
    #             break


    # def archive_model(self, model_id):
    #     '''
    #     Extract model data.
    #     '''
    #     # Create output directory for model archives
    #     model_data = Tools.get_json_with_retry(f"{self.base_url}/{model_id}?{urllib.parse.urlencode({ "nsfw": "true" })}", self.token, self.retry_delay)

    #     # Add model data to the summary.
    #     user = 'Unknown'
    #     if 'creator' in model_data and 'username' in model_data['creator']:
    #         user = model_data['creator']['username']

    #     self.build_tasks(user, model_data)


    def build_tasks(self, usernames:list = None, modelIds:list = None) -> Model:
        '''
        Do the extraction of model data.
        '''

        result = self.metadata_extractor.extract(usernames=usernames, model_ids=modelIds)

        for modeil_id, model in result.items():

            print(f"Model ID: {modeil_id}")

            for version in model.versions:

                print(f"Version ID: {version.id}")

                for file in version.files:
                    print(f"file ID: {file.id}")

                for asset in version.assets:
                    print(f"Asset ID: {asset.id}")



        # username            = Tools.sanitize_name(username, max_length=self.max_path_length)
        # model_id            = model_data['id']
        # model_name          = Tools.sanitize_name(model_data['name'], max_length=self.max_path_length)
        # model_type          = model_data['type']
        # current_model       = Model(model_id, model_name, model_type, model_data['description'])
        # model_ouput_path    = os.path.join(self.output_dir, username, f'{model_name} ({model_type})')

        # current_model.tasks.append(WriteMetadata(f'{model_id}.json', model_ouput_path, model_data))
        # current_model.tasks.append(WriteDescription(model_ouput_path, model_data['description']))

        # # Loop through the model versions.
        # for version in model_data['modelVersions']:

        #     # Get fields from model version data
        #     version_base_model      = version['baseModel'] if version['baseModel'] else ''
        #     current_version         = Version(model_id, version['name'], version_base_model)
        #     version_output_path     = os.path.join(model_ouput_path, f'{version["name"]} ({version_base_model})')

        #     current_version.tasks.append(WriteTrainedWords(version_output_path, version.get('trainedWords', [])))

        #     if self.only_base_models is not None and version_base_model.upper() not in self.only_base_models:
        #         self.logger.warning("Skipping condition %s, not in wanted model list", model_name)
        #         continue

        #     for model_file in version['files']:
        #         model_hash = ''

        #         if 'hashes' in model_file and 'SHA256' in model_file['hashes']:
        #             model_hash = model_file['hashes']['SHA256']

        #         current_version.tasks.append(DownloadFile(self.token,
        #                                                 model_file['name'],
        #                                                 version_output_path,
        #                                                 model_file['downloadUrl'],
        #                                                 model_hash,
        #                                                 model_file['sizeKB'],
        #                                                 retry_delay=self.retry_delay,
        #                                                 skip_existing_verification=self.skip_existing_verification))

        #     for idx, model_image in enumerate(version['images']):
        #         file_extension = Tools.get_file_extension_regex(model_image['url'])
        #         current_version.tasks.append(DownloadFile(self.token,
        #                                                   f'{idx}.{file_extension}',
        #                                                   version_output_path,
        #                                                   model_image['url'],
        #                                                   retry_delay=self.retry_delay,
        #                                                   skip_existing_verification=self.skip_existing_verification))

        #     current_model.versions.append(current_version)

        # self.add_to_download_summary(username, current_model)


    # def add_to_download_summary(self, username: str, model: Model):
    #     '''
    #     Helper method to init the models to and empty array before adding one.
    #     '''
    #     if username not in self.work_summary:
    #         self.work_summary[username] = []

    #     self.work_summary[username].append(model)


    def summerise(self):
        '''
        Write the summary information for the user.
        '''
        summary = os.linesep
        summary += 'Below are a list of the requested tasks (Note: anything already downloaded will be skipped).'
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
                    summary += f"\t\tVersion: {v.id} ({v.name}) based on {v.base_model}" + os.linesep
                    summary += "\t\t\tTasks:" + os.linesep
                    for t in v.tasks:
                        summary += f"\t\t\t\t{t.name}" + os.linesep
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
