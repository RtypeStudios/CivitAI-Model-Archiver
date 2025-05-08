import logging
import os

from common.tools import Tools
from models.model import Model
from tasks.download_file import DownloadFile
from tasks.task import Task
from tasks.write_description import WriteDescription
from tasks.write_metadata import WriteMetadata
from tasks.write_trained_words import WriteTrainedWords

class TaskBuilder:

    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self, output_dir:str, token:str, max_tries:int, retry_delay:int, max_threads:int, only_base_models:list[str], skip_existing_verification:bool, skip_compress_models:bool):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.output_dir = Tools.sanitize_directory_name(output_dir)
        self.token = token
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.max_threads = max_threads
        self.skip_existing_verification = skip_existing_verification
        self.skip_compress_models = skip_compress_models

        if only_base_models is not None:
            self.only_base_models = [s.upper() for s in only_base_models]
        else:
            self.only_base_models = None


    def build_tasks(self, models:dict[str, Model]) -> list[Task]:
        '''
        Do the extraction of model data.
        '''
        tasks = []

        for model_id, file in models.items():

            if not os.path.exists(os.path.join(self.output_dir, file.output_path, f'{model_id}.json')):
                tasks.append(WriteMetadata(model_id, os.path.join(self.output_dir, file.output_path), file.metadata))

            if not os.path.exists(os.path.join(self.output_dir, file.output_path, 'description.html')):
                tasks.append(WriteDescription(os.path.join(self.output_dir, file.output_path), file.description))

            for version in file.versions:

                if self.only_base_models is not None and version.base_model.upper() not in self.only_base_models:
                    self.logger.warning("Skipping condition: %s, not in wanted base model list", version.base_model)
                    continue

                if not os.path.exists(os.path.join(self.output_dir, version.output_path, 'trained_words.txt')):
                    tasks.append(WriteTrainedWords(os.path.join(self.output_dir, version.output_path), version.trained_words))

                for file in version.files:

                    temp_output_path        = os.path.join(self.output_dir, file.output_path, f'{file.name}.tmp') 
                    # compressed_output_path  = os.path.join(self.output_dir, file.output_path, f'{file.name}.7z') 
                    # downloaded_output_path  = os.path.join(self.output_dir, file.output_path, file.name)

                    # # If compressed version exists, job done!
                    # if os.path.exists(compressed_output_path):
                    #     continue

                    # # If file excists but isn't compressed, verify and compress the file.
                    # elif os.path.exists(downloaded_output_path):
                    #     continue

                    # # If partial file is present or file doesn't exists, download or resume the file
                    # elif os.path.exists(temp_output_path) or not os.path.exists(downloaded_output_path):
                    tasks.append(DownloadFile(self.token,
                                                file.name,
                                                os.path.join(self.output_dir, file.output_path),
                                                file.url,
                                                os.path.exists(temp_output_path),
                                                self.retry_delay,
                                                self.max_tries,
                                                file.sha_256_hash,
                                                file.size_kb,
                                                skip_existing_verification=self.skip_existing_verification,
                                                compress=not self.skip_compress_models))



                for asset in version.assets:

                    if not os.path.exists(os.path.join(self.output_dir, asset.output_path, asset.name)):
                        tasks.append(DownloadFile(self.token,
                                                asset.name,
                                                os.path.join(self.output_dir, asset.output_path),
                                                asset.url,
                                                False,
                                                self.retry_delay,
                                                self.max_tries,
                                                skip_existing_verification=self.skip_existing_verification))

        return tasks