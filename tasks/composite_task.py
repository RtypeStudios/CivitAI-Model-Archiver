import os
from pathlib import Path
import py7zr
from tasks.task import BaseTask

class CompositeTask(BaseTask):

    def __init__(self, tasks:list[BaseTask]):
        super().__init__(f'Composite Task', "", "")
        self.tasks = tasks
        
    def run(self) -> bool:
        '''
        Run the composite task.
        '''
        for task in self.tasks:
            task.run()