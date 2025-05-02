import logging

class Model:
    '''
    Class representing a machine learning model.
    Each model can have multiple versions and tasks associated with it.
    '''
    def __init__(self, model_id:int, model_name:str, model_type:str, model_description:str):
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.id = model_id
        self.name = model_name
        self.type = model_type
        self.description = model_description
        self.versions = []
        self.tasks = []