import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from tqdm import tqdm

from common.tools import Tools
from models.model import Model
from tasks.download_file import DownloadFile
from tasks.download_file_2 import DownloadFile2
from tasks.task import Task
from tasks.write_description import WriteDescription
from tasks.write_metadata import WriteMetadata
from tasks.write_trained_words import WriteTrainedWords


class Processor:

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

        self.work_summary = {}
        self.base_url = "https://civitai.com/api/v1/models"
        self.max_path_length = 200

        self.logger.info("Processor initialized with output_dir: %s, max_tries: %d, retry_delay: %d, max_threads: %d, Skip existing verification: %s", self.output_dir, self.max_tries, self.retry_delay, self.max_threads, self.skip_existing_verification)

        if self.only_base_models is not None:
            self.logger.info("Only fetching models versions based on: %s.n" \
            "", "".join(self.only_base_models))


    def build_tasks(self, models:dict[str, Model]) -> list[Task]:
        '''
        Do the extraction of model data.
        '''

        tasks = []

        for model_id, model in models.items():

            tasks.append(WriteMetadata(model_id, os.path.join(self.output_dir, model.output_path), model.metadata))
            tasks.append(WriteDescription(os.path.join(self.output_dir, model.output_path), model.description))

            for version in model.versions:

                if self.only_base_models is not None and version.base_model.upper() not in self.only_base_models:
                    self.logger.warning("Skipping condition: %s, not in wanted base model list", version.name)
                    continue

                tasks.append(WriteTrainedWords(os.path.join(self.output_dir, version.output_path), version.trained_words))

                for model in version.files:
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
                    tasks.append(DownloadFile2(self.token,
                                              asset.name,
                                              os.path.join(self.output_dir, asset.output_path),
                                              asset.url,
                                              self.retry_delay,
                                              self.max_tries,
                                              skip_existing_verification=self.skip_existing_verification))

        return tasks


    def summerise(self, tasks:list[Task]) -> None:
        '''
        Write the summary information for the user.
        '''
        summary = os.linesep
        summary += os.linesep
        summary += 'Below are a list of the requested tasks (Note: anything already downloaded will be skipped).'
        summary += os.linesep

        for task in tasks:
            summary += f"\t{task.name}" + os.linesep

        self.logger.info(summary)



    def do_work(self, tasks:list[Task]) -> None:
        '''
        Actually start doing the donwload.
        '''
        self.logger.info("Starting work.")
        self.logger.info("Output directory: %s", self.output_dir)
        self.logger.info("Max threads: %s", self.max_threads)
        self.logger.info("Max tries: %s", self.max_tries)
        self.logger.info("Retry delay: %s seconds", self.retry_delay)

        random.shuffle(tasks)

        with tqdm(total=len(tasks), desc="Procesing Tasks", unit="task", colour='green') as pbar:
            with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
                futures = []

                for task in tasks:
                    futures.append(executor.submit(task.run))

                for future in as_completed(futures):
                    pbar.update(1)
                    future.result()

                    # Check if the future raised an exception
                    if future.exception() is not None:
                        e = future.exception()
                        logging.error("%s error occurred: %s", type(e), e, stack_info=True, exc_info=True)
