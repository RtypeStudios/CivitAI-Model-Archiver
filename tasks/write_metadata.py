import json
import os

from common.tools import Tools
from tasks.task import Task

class WriteMetadata(Task):
    '''
    Write metadata to a JSON file.
    '''
    def __init__(self, file_name:str, output_path:str, metadata:str):
        super().__init__(f'Write Metadata: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.metadata = metadata

    def run(self):
        '''
        Write metadata to a JSON file.
        '''
        self.logger.debug('Writing Metadata')
        Tools.write_file(os.path.join(self.output_path, self.file_name), json.dumps(self.metadata, indent=4))
        return True