import logging
import os
from tasks.task import Task

class TaskSummariser:

    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

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