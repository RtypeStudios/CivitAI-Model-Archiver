import logging
import time
import argparse
import sys

from core.metadata_extractor import MetadataExtractor
from core.task_builder import TaskBuilder
from core.task_runner import TaskRunner
from core.task_summariser import TaskSummariser

if __name__ == "__main__":

    # Set up logging to both file and console.
    log_file = f"log-{time.strftime('%Y%m%d%H%M%S')}.log"
    file_logger = logging.FileHandler(log_file, encoding='utf-8')
    file_logger.setLevel(logging.DEBUG)
    
    stream_logger = logging.StreamHandler()
    stream_logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',handlers=[file_logger, stream_logger])

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Argument parsing.
    parser = argparse.ArgumentParser(description="Download model files and images from Civitai API.")
    parser.add_argument("--usernames", nargs='+', type=str, help="Enter one or more usernames you want to download from.")
    parser.add_argument("--models", nargs='+', type=str, help="Enter one or more models you want to download.")
    parser.add_argument("--retry_delay", type=int, default=10, help="Retry delay in seconds.")
    parser.add_argument("--max_tries", type=int, default=10, help="Maximum number of retries.")
    parser.add_argument("--max_threads", type=int, default=5, help="Maximum number of concurrent threads. Too many produces API Failure.")
    parser.add_argument("--token", type=str, default=None, help="API Token for Civitai.")
    parser.add_argument("--output_dir", type=str, default='model_archives', help="The place to output the downloads, defaults to 'model_archives'.")
    parser.add_argument("--only_base_models", nargs='+', type=str, help="Filter model version by the base model they are built on (SDXL, SD 1.5, Pony, Flux, ETC) see readme for list.")
    parser.add_argument("--only_model_file_types", nargs='+', type=str, help="Only download specific model types with sepcifc extensions (.ckpt, .safetensors, .pt).")
    parser.add_argument("--skip_compress_models", action='store_true', default=False, help="Do not compress models after download.")
    args = parser.parse_args()

    # Validate input arguments.
    if args.token is None:
        args.token = input("Please enter your Civitai API token: ")

    if args.usernames is None and args.models is None:
        logger.error("Please provide at least one username or model id.")
        sys.exit(1)


    logger.info(f"Logging this session to {log_file}.")

    # Build Extractor.
    extractor = MetadataExtractor(args.token, args.max_tries, args.retry_delay)

    # Task Builder
    builder = TaskBuilder(args.output_dir,
                          args.token,
                          args.max_tries,
                          args.retry_delay,
                          args.only_base_models,
                          args.only_model_file_types,
                          args.skip_compress_models)

    # Task Summariser
    task_summariser = TaskSummariser()

    # Task Runner
    task_runner = TaskRunner(args.max_threads)

    # Extract models from CivitAI.
    logger.info(f"Extracting Models from CivitAI.")
    models = extractor.extract(usernames=args.usernames, model_ids=args.models)

    # Generate work list.
    logger.info(f"Building tasks based on metadata:")
    tasks = builder.build_tasks(models)

    if len(tasks) == 0:
        logger.warning("No tasks to do, exiting.")
        sys.exit(1)

    # Summerise the work list.
    task_summariser.summerise(tasks)

    while True:
        proceed = input("Do you want to continue? (y/n): ")
        if proceed.lower() == 'n':
            print("Exiting.")
            sys.exit(1)
        elif proceed.lower() == 'y':
            print("Continuing...")
            break

    task_runner.do_work(tasks)
