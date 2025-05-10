from pathlib import Path

class Asset:
    '''
    Class representing a machine learning model.
    Each model can have multiple versions and tasks associated with it.
    '''
    def __init__(self, version, asset:dict):
        '''
        Initialize the model with url.
        '''
        self.version = version

        self.url = asset.get('url', '')
        self.type = asset.get('type', 'Unknown')

        if self.url != '':
            path = Path(self.url)
            self.id = path.stem
            self.extension = path.suffix
            self.name = path.name
        else:
            self.id = ''
            self.extension = ''
            self.name = ''

        self.output_path = self.version.output_path