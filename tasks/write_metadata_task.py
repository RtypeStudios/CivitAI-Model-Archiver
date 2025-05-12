import json
import os

from common.tools import Tools
from common.base_task import BaseTask

class WriteMetadataTask(BaseTask):
    '''
    Write metadata to a JSON file.
    '''
    def __init__(self, output_path_and_file_name:str, metadata:str):
        super().__init__(f'Write Metadata: \"{output_path_and_file_name}\"')
        self.metadata = metadata

    def run(self):
        '''
        Write metadata to a JSON file.
        '''
        self.logger.debug('Writing Metadata')
        Tools.write_file(self.output_path_and_file_name, json.dumps(self.metadata, indent=4))
        return True