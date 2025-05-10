import hashlib
import os
import time

from tqdm import tqdm

from common.base_task import BaseTask

class VerifyFileTask(BaseTask):
    '''
    Verify the SHA256 hash of a file.
    '''
    def __init__(self, input_path_and_file_name:str, output_path_and_file_name:str, expected_sha256_hash:str):
        super().__init__(f'Verify File: \"{input_path_and_file_name}\" with hash \"{expected_sha256_hash}\"', input_path_and_file_name, output_path_and_file_name)
        self.expected_sha256_hash = expected_sha256_hash

    def run(self) -> bool:
        '''
        Verify the SHA256 hash of a file.
        '''
        sha256 = hashlib.sha256()
        filesize = os.path.getsize(self.input_path_and_file_name)

        with tqdm(desc="Verifying Download", total=filesize, unit='B', unit_scale=True, leave=False, colour='blue') as progress_bar:
            with open(self.input_path_and_file_name, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    progress_bar.update(len(chunk))
                    sha256.update(chunk)

        if sha256.hexdigest().upper() == self.expected_sha256_hash.upper():
            os.rename(self.input_path_and_file_name, self.output_path_and_file_name)
            return True
        else:
            renamed = self.output_path_and_file_name + f'.failed_verify_{time.strftime('%Y%m%d%H%M%S')}'
            self.logger.debug('Error \"%s\" failed hash verifcation, renamed to: \"%s\"', self.input_path_and_file_name, renamed)
            os.rename(self.input_path_and_file_name, renamed)
            return False
