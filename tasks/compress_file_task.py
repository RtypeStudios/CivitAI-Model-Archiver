import os
from pathlib import Path
import threading
import time
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


            # total_size = os.path.getsize(self.input_path_and_file_name)
                
            # This is becuase there appears to be no mechansim in py7zr to track archiving progress.
            # It is kludgey, but it works.
            task_done = False

            with tqdm(unit='b', total=os.path.getsize(self.input_path_and_file_name), unit_scale=False, desc="Compressing (rough estimate)", colour='blue') as progress_bar:

                def monitor_progress():
                    while not os.path.exists(self.output_path_and_file_name):
                        time.sleep(0.1)  # Wait for the file to be created.
                    while task_done is False:
                        progress_bar.n = os.path.getsize(self.output_path_and_file_name)
                        progress_bar.refresh()
                        time.sleep(0.5)  # Check progress every 0.5 seconds.
                    progress_bar.close()
                    return

                monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
                monitor_thread.start()

                with py7zr.SevenZipFile(self.output_path_and_file_name, 'w') as archive:
                    archive.writeall(self.input_path_and_file_name, arcname=Path(self.input_path_and_file_name).name)
                    task_done = True
                    monitor_thread.join()


            # with tqdm(unit='File', unit_scale=False, total=1, desc="Testing Archive") as progress_bar:
            #     with py7zr.SevenZipFile(self.output_path_and_file_name, 'w') as archive:
            #         if archive.testzip() is not None:
            #             self.logger.debug("Compressed file failed test: %s", self.output_path_and_file_name)
            #             self.cleanup()
            #             return False
            #         else:
            #             progress_bar.update(1)


            self.logger.debug("Compressing successful, removing exiting %s", self.input_path_and_file_name)

            if os.path.exists(self.output_path_and_file_name):
                os.remove(self.input_path_and_file_name)
            else:
                self.logger.debug("Compressed file does not exist, assuming it was removed by the user: %s", self.output_path_and_file_name)

            return True

        except (Exception) as e:
            self.logger.error("Compressing failed, removed partially compressed file: %s", self.output_path_and_file_name, type(e), e, stack_info=True, exc_info=True)
            self.cleanup()
            return False

    def cleanup(self) -> bool:
        '''
        remove the file if it exists.
        '''
        if os.path.exists(self.output_path_and_file_name):
            os.remove(self.output_path_and_file_name)