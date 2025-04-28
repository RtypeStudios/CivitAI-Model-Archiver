from .task import Task

class Download(Task):
    def __init__(self, file_name:str, output_path:str, url:str, sha256_hash='', file_size=0, success=True, reason=''):
        super().__init__(f'Download File: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.url = url
        self.sha256_hash = sha256_hash
        self.file_size = file_size
        self.success = success
        self.reason = reason