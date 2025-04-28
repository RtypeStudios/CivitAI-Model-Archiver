import json
import os
import re
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
    def sanitize_name(name, folder_name=None, max_length=200, subfolder=None, output_dir=None, username=None):
        """Sanitize a name for use as a file or folder name."""
        base_name, extension = os.path.splitext(name)

        if folder_name and base_name == folder_name:
            return name

        if folder_name:
            base_name = base_name.replace(folder_name, "").strip("_")

        # Remove problematic characters and control characters
        base_name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]', '_', base_name)

        # Handle reserved names (Windows specific)
        reserved_names = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
        if base_name.upper() in reserved_names:
            base_name = '_'

        # Reduce multiple underscores to single and trim leading/trailing underscores and dots
        base_name = re.sub(r'__+', '_', base_name).strip('_.')
        
        # Calculate max length of base name considering the path length
        if subfolder and output_dir and username:
            path_length = len(os.path.join(output_dir, username, subfolder))
            max_base_length = max_length - len(extension) - path_length
            base_name = base_name[:max_base_length].rsplit('_', 1)[0]

        sanitized_name = base_name + extension
        return sanitized_name.strip()