import logging
import os

from common.tools import Tools
from models.model import Model
from tasks.download_file_2 import DownloadFile2
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

        for model_id, model in models.items():

            if not os.path.exists(os.path.join(self.output_dir, model.output_path, f'{model_id}.json')):
                tasks.append(WriteMetadata(model_id, os.path.join(self.output_dir, model.output_path), model.metadata))

            if not os.path.exists(os.path.join(self.output_dir, model.output_path, 'description.html')):
                tasks.append(WriteDescription(os.path.join(self.output_dir, model.output_path), model.description))

            for version in model.versions:

                if self.only_base_models is not None and version.base_model.upper() not in self.only_base_models:
                    self.logger.warning("Skipping condition: %s, not in wanted base model list", version.name)
                    continue

                if not os.path.exists(os.path.join(self.output_dir, version.output_path, 'trained_words.txt')):
                    tasks.append(WriteTrainedWords(os.path.join(self.output_dir, version.output_path), version.trained_words))

                for model in version.files:

                    model_path = os.path.join(self.output_dir, model.output_path, model.name)

                    if not self.skip_compress_models:
                        model_path = model_path + '.7z'   

                    if not os.path.exists(model_path):
                        tasks.append(DownloadFile2(self.token,
                                                model.name,
                                                os.path.join(self.output_dir, model.output_path),
                                                model.url,
                                                self.retry_delay,
                                                self.max_tries,
                                                model.sha_256_hash,
                                                model.size_kb,
                                                skip_existing_verification=self.skip_existing_verification,
                                                compress=not self.skip_compress_models))

                for asset in version.assets:

                    if not os.path.exists(os.path.join(self.output_dir, asset.output_path, asset.name)):
                        tasks.append(DownloadFile2(self.token,
                                                asset.name,
                                                os.path.join(self.output_dir, asset.output_path),
                                                asset.url,
                                                self.retry_delay,
                                                self.max_tries,
                                                skip_existing_verification=self.skip_existing_verification))

        return tasks