import json
import logging
import urllib.parse

from common.tools import Tools
from models.model import Model

class MetadataExtractor:

    '''
    Class to process the model data and download files from CivitAI.
    '''
    def __init__(self, token:str=''):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.base_url = "https://civitai.com/api/v1/models"
        self.token = token
        self.retry_delay = 20



    # ------------------------------------
    # Main Worker.
    # ------------------------------------

    def extract(self, usernames:list=None, model_ids:list=None):
        '''
        Extract all models for a given user or model ID.
        '''

        models = []

        if usernames is not None:
            for u in usernames:
                user_models = self.__extract_user(u)
                for m in user_models:
                    models.append(m)
        
        if model_ids is not None:
            for m in model_ids:
                models.append(self.__extract_model(m))

        result = {}

        for model in models:
            if model.id not in result:
                result[model.id] = []
            result[model.id].append(model)

        print(json.dumps(result, default=lambda o: o.__dict__, indent=4))

        return result

    def __extract_user(self, username:str):
        '''
        Exctract all models for a given user.
        '''
        models = []

        page = f"{self.base_url}?{urllib.parse.urlencode({ "username": username, "nsfw": "true" })}"

        while True:
            if page is None:
                self.logger.info("End of pagination reached: 'next_page' is None.")
                break

            data = Tools.get_json_with_retry(page, self.token, self.retry_delay)

            for model in data['items']:
                models.append(Model(model))

            metadata = data.get('metadata', {})
            page = metadata.get('nextPage')

            if not metadata and not data['items']:
                self.logger.warning("Termination condition met: 'metadata' is empty.")
                break

        return models

    def __extract_model(self, model_id:str):
        '''
        Exctract all models for a model.
        '''
        data = Tools.get_json_with_retry(f"{self.base_url}/{model_id}?{urllib.parse.urlencode({ "nsfw": "true" })}", self.token, self.retry_delay)
        return Model(data)
