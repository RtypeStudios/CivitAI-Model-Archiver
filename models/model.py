import os
from common.tools import Tools
from models.version import Version

class Model:
    '''
    Class representing a machine learning model.
    Each model can have multiple versions and tasks associated with it.
    '''
    def __init__(self, model:dict):
        '''
        Initialize the model with its ID, name, type, and description.
        '''
        self.id             = model.get('id', '0')
        self.name           = Tools.sanitize_name(model.get('name', 'Unknown'))
        self.type           = Tools.sanitize_name(model.get('type', 'Unknown'))
        self.description    = model.get('description', '')
        self.metadata       = model

        if 'creator' in model and 'username' in model['creator']:
            self.username = model['creator']['username']
        else:
            self.username = 'Unknown'

        self.output_path = os.path.join(self.username, f'{self.name} ({self.type})')

        self.versions = []

        for model_version in model['modelVersions']:
            self.versions.append(Version(self, model_version))

        

