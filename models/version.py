'''
Module for managing model versions
'''
from models.asset import Asset
from models.file import File

class Version:
    '''
    Class representing a version of a model.
    Each version is associated with a specific model and can have multiple tasks.
    '''
    def __init__(self, model, version:dict):
        '''
        Initialize the version with its ID, name, and base model.
        '''
        self.model = model
        self.id = version.get('id', '0')
        self.name = version.get('name', 'Unknown')
        self.base_model = version.get('baseModel', '')
        self.created_at = version.get('createdAt', '')
        self.published_at = version.get('publishedAt', '')
        self.status = version.get('status', '')
        self.availability = version.get('availability', '')
        self.nsfw_level = version.get('nsfwLevel', '')
        self.covered = version.get('covered', '')
        self.trained_words = version.get('trainedWords', [])

        self.tasks = []

        self.files = []
        for files in version['files']:
            self.files.append(File(self, files))

        self.assets = []
        for asset in version['images']:
            self.assets.append(Asset(self, asset))
