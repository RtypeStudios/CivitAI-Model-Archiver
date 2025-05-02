import logging

class Version:
    '''
    Class representing a version of a model.
    Each version is associated with a specific model and can have multiple tasks.
    '''
    def __init__(self, version_id:int, version_name:str, base_model:str):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.id = version_id
        self.name = version_name
        self.base_model = base_model
        self.tasks = []