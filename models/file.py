'''
File class representing a model.
'''

import os
from common.tools import Tools


class File:
    '''
    Class representing a machine learning model.
    Each model can have multiple versions and tasks associated with it.
    '''
    def __init__(self, version, file:dict):
        '''
        Initialize the model with url.
        '''
        self.version        = version

        self.id             = file.get('id', '0')
        self.size_kb        = file.get('sizeKb', 0)
        self.name           = file.get('name', '')
        self.mode_type      = file.get('type', 'Unknown')
        self.url            = file.get('downloadUrl')
        self.primary        = file.get('primary')

        self.sha_256_hash = ''

        if 'hashes' in file:
            if 'SHA256' in file['hashes']:
                self.sha_256_hash = file['hashes']['SHA256']

        self.output_path = self.version.output_path