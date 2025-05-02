from tasks.task import Task

class WriteTrainedWords(Task):
    '''
    Write trained words to a text file.
    '''
    def __init__(self, output_path:str, trained_words:str):
        file_name = 'trained_words.txt'
        super().__init__(f'Write Trained Words: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.trained_words = "\n".join(trained_words)