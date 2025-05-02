from lxml import etree, html

from tasks.task import Task

class WriteDescription(Task):
    '''
    Write a description to an HTML file.
    '''
    def __init__(self, output_path:str, description:str):
        file_name = 'description.html'
        super().__init__(f'Write Description: \"{file_name}\" to: \"{output_path}\"', output_path, file_name)

        if description is None or description == '':
            self.description = ''
        else:
            self.description = etree.tostring(html.fromstring(description), encoding='utf8', pretty_print=True).decode('utf-8')