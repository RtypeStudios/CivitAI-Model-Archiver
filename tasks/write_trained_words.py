import os
from common.tools import Tools
from tasks.task import Task

class WriteTrainedWords(Task):
    '''
    Write trained words to a text file.
    '''
    def __init__(self, output_path:str, trained_words:str):
        self.file_name = 'trained_words.txt'
        super().__init__(f'Write Trained Words: \"{self.file_name}\" to: \"{output_path}\"', output_path, self.file_name)
        self.trained_words = trained_words

    def run(self):
        '''
        Write the trained word list to a text file.
        '''
        self.logger.debug('Writing Metadata')
        Tools.write_file(os.path.join(self.output_path, self.file_name), "\n".join(self.trained_words))
        return True;