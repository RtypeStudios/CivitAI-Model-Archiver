import os
from pathlib import Path
import py7zr
from tqdm import tqdm

from common.base_task import BaseTask

class CompressFileTask(BaseTask):
    '''
    Compress a file using 7zip.
    '''
    def __init__(self, input_path_and_file_name:str, output_path_and_file_name:str):
        super().__init__(f'Compress File: \"{input_path_and_file_name}\" to: \"{output_path_and_file_name}\"', input_path_and_file_name, output_path_and_file_name)
        
    def run(self) -> bool:
        '''
        Verify the SHA256 hash of a file.
        '''
        try:

            self.logger.debug("Compressing file %s to %s.", self.input_path_and_file_name, self.output_path_and_file_name)

            if os.path.exists(self.input_path_and_file_name) and os.path.exists(self.output_path_and_file_name):
                self.logger.debug("Both input file and output file exist, assuming interrupted partial compression, removing %s and starting again.", self.output_path_and_file_name)
                os.remove(self.output_path_and_file_name)

            with tqdm(desc="Compressing/Testing Archive (PROGRESS INDICATOR NOT WORKING)", total=2, unit='B', unit_scale=True, leave=False, colour='blue') as progress_bar:
                with py7zr.SevenZipFile(self.output_path_and_file_name, 'w', filters=[{"id": py7zr.FILTER_LZMA2, "preset": 7}]) as archive:
                    
                    # Comrpess the file.
                    archive.write(self.input_path_and_file_name, Path(self.input_path_and_file_name).name)
                    progress_bar.update(1)

                    # Test the archive.
                    if archive.testzip() is not None:
                        self.logger.debug("Compressed file failed test: %s", self.output_path_and_file_name)
                        self.cleanup()
                        return False
                    else:
                        progress_bar.update(2)

            self.logger.debug("Compressing successful, removing exiting %s", self.input_path_and_file_name)

            if os.path.exists(self.output_path_and_file_name):
                os.remove(self.input_path_and_file_name)
            else:
                self.logger.debug("Compressed file does not exist, assuming it was removed by the user: %s", self.output_path_and_file_name)

            return True

        except (Exception) as e:
            self.logger.debug("Compressing failed, removed partially compressed file: %s", self.output_path_and_file_name)
            self.cleanup()
            return False

    def cleanup(self) -> bool:
        '''
        remove the file if it exists.
        '''
        if os.path.exists(self.output_path_and_file_name):
            os.remove(self.output_path_and_file_name)