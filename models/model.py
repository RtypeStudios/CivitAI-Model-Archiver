# Data Models

class Model:
    def __init__(self, model_id:int, model_name:str, model_type:str, model_description:str):
        self.id = model_id
        self.name = model_name
        self.type = model_type
        self.description = model_description
        self.versions = []
        self.tasks = []