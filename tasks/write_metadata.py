import json

from .task import Task

class WriteMetadata(Task):
    def __init__(self, file_name:str, output_path:str, metadata:str):
        super().__init__(f'Write Metadata: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.metadata = json.dumps(metadata, indent=4)