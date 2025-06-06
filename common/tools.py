import json
import os
import re
import string
import sys
import time
import requests

class Tools:
    '''
    Collection of helper functions for various tasks.
    '''
    def __new__(cls):
        raise TypeError('Static classes cannot be instantiated')

    @staticmethod
    def sanitize_directory_name(name):
        '''
        Sanitize the directory name by removing invalid characters and limiting length.
        '''
        return name.rstrip()  # Remove trailing whitespace characters

    @staticmethod
    def write_file(file_path, content):
        '''
        Write the content to a file, creating directories as needed.
        '''
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def get_json_with_retry(logger, url, token, retry_delay, retry_count=0, max_retries=3):
        '''
        Make a GET request to the given URL and return the JSON response, with some retry logic built in.
        '''
        data = None
        retry_count = 0
        while retry_count < max_retries:
            try:
                with requests.get(url, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}) as response:
                    
                    if response.status_code == 401:
                        logger.debug("Unauthorized for url (Model Removed?): %s, Reason: %s", url, response.reason)
                        return None

                    if response.status_code == 404:
                        logger.debug("Not found (Model Removed?): %s, Reason: %s", url, response.reason)
                        return None
                    
                    response.raise_for_status()
                    
                    data = response.json()

                break  # Exit retry loop on successful response
            except (requests.RequestException, TimeoutError, json.JSONDecodeError) as e:
                logger.warn(f"Error making API request or decoding JSON response: %s", e)
                retry_count += 1
                if retry_count < max_retries:
                    logger.warn(f"Retrying in %s seconds...", retry_delay)
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Maximum retries exceeded fetching %s. Exiting.", url)

        return data

    @staticmethod
    def sanitize_name(value, max_length=200):
        '''
        Sanitize a name for use as a file or folder name.
        '''
        printable = set(string.printable)
        value = ''.join(filter(lambda x: x in printable, value))

        # This are typically dividers
        value = value.replace('|', '-')
        value = value.replace('/', '-')

        # The rest of these cause issues on windows.
        value = re.sub(r'[\\:*?"<>]', '_', value)

        # Reduce multiple underscores to single and trim leading/trailing underscores and dots
        value = re.sub(r'__+', '_', value).strip('_.')

        value = re.sub(r"\s+", " ", value)

        # remove trailing dashes
        if value.endswith('-'):
            value = value[:-1]

        return value.strip()[:max_length]
