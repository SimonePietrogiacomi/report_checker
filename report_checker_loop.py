from report_checker_updated import SingleWindowBrowserScraper
import time
# from playsound import playsound
from random import randint
import subprocess
import datetime
import os
import yaml
import logging

### start config.yaml fields ###
CONFIGURATIONS = "configurations"
LOG_FILE_NAME = "log_file_name"
OUTER_LOOP_SLEEP_TIME = "outer_loop_sleep_time"
### end config.yaml fields ###

current_file_path = os.path.realpath(__file__)
current_file_path = current_file_path[:current_file_path.rfind(os.path.sep)]

CONFIG_FILE_NAME = "config.yaml"
config_file_path = current_file_path + os.path.sep + CONFIG_FILE_NAME
CONFIG_EXPECTED_ITEMS = 3
LOGGER_NAME = "report_checker"

# get the log file name and the sleep time between each try from the config file
with open(config_file_path) as config_file:
    try:
        config_data = yaml.load(config_file, Loader=yaml.FullLoader)
        if len(config_data) != CONFIG_EXPECTED_ITEMS:
            print(f"Error! The number of keys into config file aren't {CONFIG_EXPECTED_ITEMS} but {len(config_data)}")
        else:
            try:
                log_file_name = config_data[CONFIGURATIONS][LOG_FILE_NAME]
            except Exception as e:
                print(f"There's no {LOG_FILE_NAME} field in config file. Add it!")
                exit(1)

            log_file_path = current_file_path + os.path.sep + log_file_name
            logger = logging.getLogger(LOGGER_NAME)
            logger.setLevel(logging.INFO)
            fh = logging.FileHandler(log_file_path, mode='w', delay=True)
            fh.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)-22s - %(message)s',
                                          '%Y-%m-%d %H:%M:%S')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            logger.info("Hello, congratulations on your excellent choice")
            try:
                config_sleep_time = config_data[CONFIGURATIONS][OUTER_LOOP_SLEEP_TIME]
            except Exception as e:
                print(f"Error while reading {OUTER_LOOP_SLEEP_TIME} in config file")
                logger.error(f"Error while reading {OUTER_LOOP_SLEEP_TIME} in config file")
                logger.error(e)
                exit(1)
    except Exception as e:
        print(f"Bad YAML syntax in \"{CONFIG_FILE_NAME}\"")
        logger.error(f"Bad YAML syntax in \"{CONFIG_FILE_NAME}\"")
        logger.error(e)
        exit(1)

# True if there are changes in the site
report_submitted = False

# Loop over the report checker until there are changes in the site
while not report_submitted:
    browser_scraper = SingleWindowBrowserScraper()
    browser_scraper.predefined_run()
    report_submitted = browser_scraper.target_found
    if report_submitted:
        # works under linux, it sends you a notify
        subprocess.Popen(['notify-send', "Risultati usciti!", "Aoh movete che so usciti!"])
        # Play a sound, it's useful when you go to the bathroom
        # playsound('/path/to/file.mp3')
    else:
        sleep_time = randint(config_sleep_time[0], config_sleep_time[1])
        print(f"{datetime.datetime.now()} - Check completed")
        print(f"Waiting {datetime.timedelta(seconds=sleep_time)} minutes")
        logger.info(f"Waiting {datetime.timedelta(seconds=sleep_time)} minutes")
        time.sleep(sleep_time)
        print("------")
