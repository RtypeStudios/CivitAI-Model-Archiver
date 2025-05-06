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

    def extract(self, usernames:list=None, model_ids:list=None) -> dict[str, Model]:
        '''
        Extract all models for a given user or model ID.
        '''

        result = {}

        if usernames is not None:
            for u in usernames:
                user_models = self.__extract_user(u)
                for m in user_models:
                    if m.id not in result:
                        result[m.id] = m
        
        if model_ids is not None:
            for m in model_ids:
                if m not in result:
                    result[m] = self.__extract_model(m)

        return result


    def __extract_user(self, username:str):
        '''
        Extract all models for a given user.
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
