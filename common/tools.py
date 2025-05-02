import json
import os
import re
import sys
import time
import unicodedata
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
    def get_file_extension_regex(url):
        '''
        Extract the file extension from the URL using regex.
        taken from: https://www.geeksforgeeks.org/get-the-file-extension-from-a-url-in-python/
        '''
        match = re.search(r'\.([a-zA-Z0-9]+)$', url)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def write_file(file_path, content):
        '''
        Write the content to a file, creating directories as needed.
        '''
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding='utf-8') as f:
            f.write(content)

    @staticmethod
    def get_json_with_retry(session, url, token, retry_delay, retry_count=0, max_retries=3):
        '''
        Make a GET request to the given URL and return the JSON response, with some retry logic built in.
        '''
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = session.get(url, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
                response.raise_for_status()
                data = response.json()
                break  # Exit retry loop on successful response
            except (requests.RequestException, TimeoutError, json.JSONDecodeError) as e:
                print(f"Error making API request or decoding JSON response: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Maximum retries exceeded. Exiting.")
                    sys.exit(1)

        return data


    @staticmethod
    def sanitize_name(name, max_length=200):
        """Sanitize a name for use as a file or folder name."""

        # Remove problematic characters and control characters
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]', '_', name)

        # Reduce multiple underscores to single and trim leading/trailing underscores and dots
        name = re.sub(r'__+', '_', name).strip('_.')
    
        return name.strip()[:max_length]  # Limit length to max_length

    # @staticmethod
    # def clean(name):
    #     """
    #     Clean a string to make it safe for use in filesystems.
    #     """
    #     # Normalize Unicode characters to their closest ASCII equivalent
    #     name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    #     # Remove invalid filesystem characters
    #     name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)

    #     # Remove leading/trailing whitespace and dots
    #     name = name.strip().strip('.')

    #     # Replace multiple consecutive underscores with a single underscore
    #     name = re.sub(r'__+', '_', name)

    #     return name