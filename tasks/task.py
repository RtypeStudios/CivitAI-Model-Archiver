import logging

class Task:
    '''
    Base class for all tasks.
    '''
    def __init__(self, name:str, output_path:str, file_name:str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.name = name
        self.type = type
        self.file_name = file_name
        self.output_path = output_path

    def run(self) -> bool:
        '''
        Run the task.
        This method should be overridden by subclasses to implement the task logic.
        '''
        raise NotImplementedError("Subclasses should implement this method.")
