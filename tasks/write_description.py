import os
from lxml import etree, html

from common.tools import Tools
from tasks.task import Task

class WriteDescription(Task):
    '''
    Write a description to an HTML file.
    '''

    def __init__(self, output_path:str, description:str):
        '''
        Initialize the task with the output path and description.
        '''
        file_name = 'description.html'
        super().__init__(f'Write Description: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)
        self.description = description


    def run(self):
        '''
        Write the description to an HTML file.
        '''
        self.logger.debug('Writing description')

        if self.description is None or self.description == '':
            self.description = ''
        else:
            self.description = etree.tostring(html.fromstring(self.description), encoding='utf8', pretty_print=True).decode('utf-8')

        Tools.write_file(os.path.join(self.output_path, self.file_name), self.description)
        return True
