import logging
import os
from pathlib import Path

from common.tools import Tools
from models.model import Model

from common.base_task import BaseTask
from tasks.composite_task import CompositeTask
from tasks.verify_file_task import VerifyFileTask
from tasks.compress_file_task import CompressFileTask
from tasks.download_file_task import DownloadFileTask
from tasks.write_description_task import WriteDescriptionTask
from tasks.write_metadata_task import WriteMetadataTask
from tasks.write_trained_words_task import WriteTrainedWordsTask

class TaskBuilder:
    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self, output_dir:str, token:str, max_tries:int, retry_delay:int, only_base_models:list[str], only_model_file_types:list[str], skip_compress_models:bool):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.output_dir = Tools.sanitize_directory_name(output_dir)
        self.token = token
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.skip_compress_models = skip_compress_models

        if only_base_models is not None:
            self.only_base_models = [s.upper() for s in only_base_models]
        else:
            self.only_base_models = None

        if only_model_file_types is not None:
            self.only_model_file_types = ['.' + s.upper() for s in only_model_file_types]
        else:
            self.only_model_file_types = None


    def build_tasks(self, models:dict[str, Model]) -> list[BaseTask]:
        '''
        Do the extraction of model data.
        '''
        tasks = []

        self.logger.info("Build tasks based on existing files at %s", self.output_dir)

        for model_id, model in models.items():

            metadata_path = os.path.join(self.output_dir, model.output_path, f'{model_id}.json')

            if not os.path.exists(metadata_path):
                tasks.append(WriteMetadataTask(metadata_path, model.metadata))

            description_path = os.path.join(self.output_dir, model.output_path, 'description.html')

            if not os.path.exists(description_path):
                tasks.append(WriteDescriptionTask(description_path, model.description))

            for version in model.versions:

                if version.availability.upper() != 'PUBLIC':
                    self.logger.warning("Skipping condition: %s, This model is not publically available.", version.name)
                    continue

                if self.only_base_models is not None and version.base_model.upper() not in self.only_base_models:
                    self.logger.warning("Skipping condition: %s, not in wanted base model list.", version.base_model)
                    continue

                trained_words_path = os.path.join(self.output_dir, version.output_path, 'trained_words.txt')

                if not os.path.exists(trained_words_path):
                    tasks.append(WriteTrainedWordsTask(trained_words_path, version.trained_words))

                for file in version.files:

                    if file.model_type.upper() == 'MODEL':
                        if self.only_model_file_types is not None and Path(file.name).suffix.upper() not in self.only_model_file_types:
                            self.logger.warning("Skipping condition: %s, not in wanted model file type list.", file.name)
                            continue

                    # Flow:
                    # Url -> X.safetensor.tmp -> X.safetensor.verify -> X.safetensor -> X.safetensor.7z
                    # Download                | Verify               | Store         | Optional Compress

                    compressed_output_path  = os.path.join(self.output_dir, file.output_path, f'{file.name}.7z') 
                    downloaded_output_path  = os.path.join(self.output_dir, file.output_path, file.name)
                    need_verify_output_path = os.path.join(self.output_dir, file.output_path, f'{file.name}.verify')
                    temp_output_path        = os.path.join(self.output_dir, file.output_path, f'{file.name}.tmp')
                    

                    if self.skip_compress_models:

                        # If downloaded version exists, job done!
                        if os.path.exists(downloaded_output_path):
                            continue

                        # File needs to be verified.
                        elif os.path.exists(need_verify_output_path):
                            tasks.append(VerifyFileTask(need_verify_output_path, downloaded_output_path, file.sha_256_hash))

                        # If partial file is present or file doesn't exist, download or resume the file, then verify.
                        else:
                            tasks.append(CompositeTask([
                                DownloadFileTask(file.url, temp_output_path, need_verify_output_path, self.token, self.retry_delay, self.max_tries, file.size_kb),
                                VerifyFileTask(need_verify_output_path, downloaded_output_path, file.sha_256_hash),
                            ], name=f'Download, Verify and Compress'))

                    else:

                        # If compressed version exists, job done!
                        if os.path.exists(compressed_output_path) and not os.path.exists(downloaded_output_path):
                            continue

                        # If file exists but isn't compressed, compress the file or if skip comrpress is set, just verify the file.
                        elif os.path.exists(downloaded_output_path):
                            # Recheck the fiel before compressing, just in case.
                            tasks.append(CompositeTask([
                                VerifyFileTask(downloaded_output_path, downloaded_output_path, file.sha_256_hash),
                                CompressFileTask(downloaded_output_path, compressed_output_path)
                            ], name=f'Reverify and Compress'))

                        # File needs to be verified, then compressed.
                        elif os.path.exists(need_verify_output_path):
                            tasks.append(CompositeTask([
                                VerifyFileTask(need_verify_output_path, downloaded_output_path, file.sha_256_hash),
                                CompressFileTask(downloaded_output_path, compressed_output_path)
                            ], name=f'Verify and Compress'))

                        # If partial file is present or file doesn't exist, download or resume the file
                        else:
                            tasks.append(CompositeTask([
                                DownloadFileTask(file.url, temp_output_path, need_verify_output_path, self.token, self.retry_delay, self.max_tries, file.size_kb),
                                VerifyFileTask(need_verify_output_path, downloaded_output_path, file.sha_256_hash),
                                CompressFileTask(downloaded_output_path, compressed_output_path)
                            ], name=f'Download, Verify and Compress'))

                for asset in version.assets:
                    downloaded_output_path = os.path.join(self.output_dir, asset.output_path, asset.name)
                    temp_output_path       = os.path.join(self.output_dir, asset.output_path, f'{asset.name}.tmp')
                    if not os.path.exists(downloaded_output_path):
                        tasks.append(DownloadFileTask(asset.url, temp_output_path, downloaded_output_path, self.token, self.retry_delay, self.max_tries))

        return tasks