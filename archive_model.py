import logging
import os
import time
import argparse
import sys

from core.processor import Processor

# Constants
#SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
#LOG_FILE_PATH = 

# logger = logging.getLogger('default')
# logger.setLevel(logging.DEBUG)
# file_handler_md = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
# file_handler_md.setLevel(logging.DEBUG)
# file_handler_md.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler_md)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler(f"log-{time.strftime('%Y%m%d%H%M%S')}.log"),
        logging.StreamHandler()
    ])


if __name__ == "__main__":

    # Argument parsing.
    parser = argparse.ArgumentParser(description="Download model files and images from Civitai API.")
    parser.add_argument("--usernames", nargs='+', type=str, help="Enter one or more usernames you want to download from.")
    parser.add_argument("--models", nargs='+', type=str, help="Enter one or more models you want to download.")
    parser.add_argument("--retry_delay", type=int, default=10, help="Retry delay in seconds.")
    parser.add_argument("--max_tries", type=int, default=3, help="Maximum number of retries.")
    parser.add_argument("--max_threads", type=int, default=5, help="Maximum number of concurrent threads. Too many produces API Failure.")
    parser.add_argument("--token", type=str, default=None, help="API Token for Civitai.")
    parser.add_argument("--output_dir", type=str, default='model_archives', help="The place to output the downloads, defaults to 'model_archives'.")
    parser.add_argument("--skip_existing_verification", action='store_true', default=False, help="Verifiy already downloaded files that have a hash value.")
    args = parser.parse_args()

    # Validate input arguments.
    if args.token is None:
        args.token = input("Please enter your Civitai API token: ")
        sys.exit(1)

    if args.usernames is None and args.models is None:
        print("Please provide at least one username or model id.")
        sys.exit(1)

    # Build processor.
    processor = Processor(args.output_dir, args.token, args.max_tries, args.retry_delay, args.max_threads, args.skip_existing_verification)

    # Process provided users.
    if args.usernames is not None:
        for u in args.usernames:
            print(f"Processing user: {u}")
            processor.archive_user(u)

    # Process provided model ids.
    if args.models is not None:
        for mid in args.models:
            print(f"Processing model with id: {mid}")
            processor.archive_model(mid)

    processor.summerise()

    while True:
        proceed = input("Do you want to continue? (y/n): ")
        if proceed.lower() == 'n':
            print("Exiting.")
            sys.exit(1)
        elif proceed.lower() == 'y':
            print("Continuing...")
            break

    processor.do_work()
