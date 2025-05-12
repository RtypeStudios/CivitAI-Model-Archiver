import os
from lxml import etree, html

from common.tools import Tools
from common.base_task import BaseTask

class WriteDescriptionTask(BaseTask):
    '''
    Write a description to an HTML file.
    '''
    def __init__(self, output_path_and_file_name:str, description:str):
        super().__init__(f'Write Description: \"{output_path_and_file_name}\"')
        self.output_path_and_file_name = output_path_and_file_name
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

        Tools.write_file(self.output_path_and_file_name, self.description)
        return True
