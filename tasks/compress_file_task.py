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

            with tqdm(desc="Compressing Download", total=1, unit='B', unit_scale=True, leave=False, colour='blue') as progress_bar:
                with py7zr.SevenZipFile(self.output_path_and_file_name, 'w', filters=[{"id": py7zr.FILTER_LZMA2, "preset": 8}]) as archive:
                    archive.write(self.input_path_and_file_name, Path(self.input_path_and_file_name).name)
                    progress_bar.update(1)

            # Stream to provide useful progres report? https://gist.github.com/reimarstier/8aa6822045dc6b562beea44799f94061
            # Testing seems to return none becuase CRC is missing?
            # with py7zr.SevenZipFile(output_path, 'r') as archive:
            #     result = archive.testzip()
            #     print(result)
            #     progress_bar.update(2)

            self.logger.debug("Compressing successful, removing %s", self.input_path_and_file_name)
            os.remove(self.input_path_and_file_name)
            return True

        except (Exception) as e:
            self.logger.debug("Compressing failed, file removed partial compression %s", self.output_path_and_file_name)
            os.remove(self.output_path_and_file_name)
            return False
