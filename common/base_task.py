import logging

class BaseTask:
    '''
    Base class for all tasks.
    '''
    def __init__(self, name:str):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.name = name
        # self.model_id = model_id
        # self.version_id = version_id

    def run(self) -> bool:
        '''
        Run the task.
        This method should be overridden by subclasses to implement the task logic.
        '''
        raise NotImplementedError("Subclasses should implement this method.")
