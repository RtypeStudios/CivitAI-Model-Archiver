import os
from lxml import etree, html

from common.tools import Tools
from common.base_task import BaseTask

class WriteDescriptionTask(BaseTask):
    '''
    Write a description to an HTML file.
    '''

    def __init__(self, output_path:str, description:str):
        '''
        Initialize the task with the output path and description.
        '''
        self.file_name = 'description.html'
        super().__init__(f'Write Description: \"{self.file_name}\" to: \"{output_path}\"', output_path, self.file_name)
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
