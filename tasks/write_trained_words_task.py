from common.tools import Tools
from common.base_task import BaseTask

class WriteTrainedWordsTask(BaseTask):
    '''
    Write trained words to a text file.
    '''
    def __init__(self, output_path_and_file_name:str, trained_words:str):
        super().__init__(f'Write Trained Words:  \"{output_path_and_file_name}\"')
        self.output_path_and_file_name = output_path_and_file_name
        self.trained_words = trained_words
        
    def run(self):
        '''
        Write the trained word list to a text file.
        '''
        self.logger.debug('Writing Metadata')
        Tools.write_file(self.output_path_and_file_name, "\n".join(self.trained_words))
        return True