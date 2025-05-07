import logging

from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from tqdm import tqdm

from tasks.task import Task

class TaskRunner:

    def __init__(self, max_threads:int=5):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.max_threads = max_threads


    def do_work(self, tasks:list[Task]) -> None:
        '''
        Actually start doing the work.
        '''
        self.logger.info("Starting work.")

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