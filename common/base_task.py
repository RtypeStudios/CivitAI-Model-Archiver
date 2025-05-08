import logging

class BaseTask:
    '''
    Base class for all tasks.
    '''
    def __init__(self, name:str, input_path_and_file_name:str, output_path_and_file_name:str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.name = name
        self.input_path_and_file_name = input_path_and_file_name
        self.output_path_and_file_name = output_path_and_file_name

    def run(self) -> bool:
        '''
        Run the task.
        This method should be overridden by subclasses to implement the task logic.
        '''
        raise NotImplementedError("Subclasses should implement this method.")
