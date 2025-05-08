import json
import os

from common.tools import Tools
from tasks.task import BaseTask

class WriteMetadataTask(BaseTask):
    '''
    Write metadata to a JSON file.
    '''
    def __init__(self, model_id:str, output_path:str, metadata:str):
        super().__init__(f'Write Metadata: \"{model_id}.json\" to: \"{output_path}\"', output_path, model_id)
        self.metadata = metadata
        self.file_name = f'{model_id}.json'

    def run(self):
        '''
        Write metadata to a JSON file.
        '''
        self.logger.debug('Writing Metadata')
        Tools.write_file(os.path.join(self.output_path, self.file_name), json.dumps(self.metadata, indent=4))
        return True