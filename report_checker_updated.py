import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.opera.options import Options as OperaOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.ie.options import Options as IEOptions
import os
import yaml
import logging
from random import randint
import datetime

### start config.yaml fields ###
AUTH = "auth"
WEBSITE_LINK = "website_link"
LOGGED_IN_WEBSITE_TITLE = "logged_in_website_title"
USERNAME_TAG_XPATH = "username_tag_xpath"
USERNAME_VALUE = "username_value"
PASSWORD_TAG_XPATH = "password_tag_xpath"
PASSWORD_VALUE = "password_value"
SUBMIT_TAG_XPATH = "submit_tag_xpath"

WEBDRIVER = "webdriver"

CONFIGURATIONS = "configurations"
LOG_FILE_NAME = "log_file_name"
PREFERRED_BROWSER_NAME = "preferred_browser_name"
HEADLESS = "headless"
NATIVE_HEADLESS_BROWSER = "native_headless_browser"
TARGET_STRING = "target_string"
TARGET_XPATH = "target_xpath"
LOGOUT_XPATHS = "logout_xpaths"
NUMBER_OF_REFRESHES = "number_of_refreshes"
REFRESH_PAGE_SLEEP_TIME = "refresh_page_sleep_time"
OUTER_LOOP_SLEEP_TIME = "outer_loop_sleep_time"
### end config.yaml fields ###

LOGGER_NAME = 'report_checker.browser'


class SingleWindowBrowserScraper:

    def __init__(self):
        """
        Its purpose is to check if a website covered by a login form has changes (a published report, a new line in a
        table, a different string, etc...). The constructor just set the correct configuration based on the config file
        """
        # Dict with the login information. It should have information about username, password and submit button
        # key = html input name
        # value = value you want to enter in this input, or "submit" if this is a submit button
        self._auth = {}

        # Dict
        # key = browser name, same used in web driver's function
        # value = absolute path of the driver
        self._webdriver = {}

        # Dict
        # key and value = go to see config file
        self._configuration = {}

        # logger
        self.logger = None

        # Link of the web page, i hope
        self._web_page_link = ""

        # Title of the desired web page, just to check if you are entering the auth data into the correct page and if
        # it login correctly
        self._logged_in_website_title = ""

        # Selected browser name
        self._browser = None

        # Current browser window
        self.current_browser = None

        # Check if he found what he is looking for
        self.target_found = False

        self._configuration = self._initial_settings()

        print(f"{datetime.datetime.now()} - Browser initialized")

    def _initial_settings(self) -> dict:
        """
        Everything you have to do to use this module is there. It reads the config file, fill the variables,
        choose the right browser and insert it in the path env

        :return: dict with the configurations from config file
        """
        current_file_path = os.path.realpath(__file__)
        current_file_path = current_file_path[:current_file_path.rfind(os.path.sep)]

        self.logger = logging.getLogger(LOGGER_NAME)

        CONFIG_FILE_NAME = "config.yaml"
        config_file_path = current_file_path + os.path.sep + CONFIG_FILE_NAME
        CONFIG_EXPECTED_KEYS = 3
        self.logger.info(f"Config YAML file in \"{config_file_path}\"")
        self.logger.info(f"Start reading config file")

        with open(config_file_path) as config_file:
            try:
                config_data = yaml.load(config_file, Loader=yaml.FullLoader)

                # check if config file has the right number of keys
                if len(config_data) != CONFIG_EXPECTED_KEYS:
                    self.logger.error(
                        f"Check YAML file \"{CONFIG_FILE_NAME}\", it should have {CONFIG_EXPECTED_KEYS} keys")
                    exit(1)

                # web driver
                try:
                    for row in config_data[WEBDRIVER]:
                        self._webdriver[row] = config_data[WEBDRIVER][row]
                    self.logger.info(f"\"{WEBDRIVER}\" read correctly")
                except Exception as e:
                    self.logger.error(f"Error while reading {WEBDRIVER} in config file")
                    self.logger.error(e)
                    exit(1)

                # auth
                try:
                    for row in config_data[AUTH]:
                        if row == WEBSITE_LINK:
                            if config_data[AUTH][row] == "":
                                self.logger.error(f"No Web Site link in \"{AUTH}\" into config file")
                                exit(1)
                            self._web_page_link = config_data[AUTH][row]
                        elif row == LOGGED_IN_WEBSITE_TITLE:
                            if config_data[AUTH][row] == "":
                                self.logger.error(f"No Web Site title in \"{AUTH}\" into config file")
                                exit(1)
                            self._logged_in_website_title = config_data[AUTH][row]
                        else:
                            if row != PASSWORD_VALUE and config_data[AUTH][row] == "":
                                self.logger.error(f"No \"{row}\" value in \"{AUTH}\" into config file")
                                exit(1)
                            self._auth[row] = config_data[AUTH][row]
                    self.logger.info(f"\"{AUTH}\" read correctly")
                except Exception as e:
                    self.logger.error(f"Error while reading {AUTH} in config file")
                    self.logger.error(e)
                    exit(1)

                configuration = {}
                # configuration
                try:
                    for row in config_data[CONFIGURATIONS]:
                        configuration[row] = config_data[CONFIGURATIONS][row]
                    self.logger.info(f"\"{CONFIGURATIONS}\" read correctly")
                except Exception as e:
                    self.logger.error(f"Error while reading {CONFIGURATIONS} in config file")
                    self.logger.error(e)
                    exit(1)
            except Exception as e:
                self.logger.error(f"Bad YAML syntax in \"{CONFIG_FILE_NAME}\"")
                self.logger.error(e)
                exit(1)
        self.logger.info(f"Config file read correctly")
        self._choose_browser(configuration[PREFERRED_BROWSER_NAME])

        # Insert in the path environment the selected driver
        try:
            os.environ["PATH"] += os.pathsep + self._webdriver[self._browser]
            self.logger.info(f"Added path env correctly: \"{self._webdriver[self._browser]}\"")
        except Exception as e:
            self.logger.error("Driver path can't be added in the env path")
            self.logger.error(e)
            exit(1)

        return configuration

    def _choose_browser(self, browser_name: str):
        """
        Check if you can use the chosen browser. If not, he decides for you

        :param browser_name: the string name of the browser you want to use
        """
        self.logger.info(f"You've chosen \"{browser_name}\" browser")
        if os.path.isfile(self._webdriver[browser_name]):
            self._browser = browser_name
            self.logger.info(f"Correctly selected {browser_name} browser")
        else:
            self.logger.error(
                f"You've selected {browser_name} but you didn't put the file in the correct folder or you didn't update config file")
            for browser in self._webdriver:
                if os.path.isfile(self._webdriver[browser]):
                    self._browser = browser
                    self.logger.info(f"{self._browser} automatically selected")
                    break
            if not self._browser:
                self.logger.error(
                    f"Download a webdriver and put the correct absolute path into config file")
                exit(1)

    def open_instance_of_browser(self, native_headless_browser: list, headless_mode: bool = False):
        """
        Open a new instance of the browser

        :param native_headless_browser: List of native headless browser. It should came from the config file
        :param headless_mode: Set if you want to run the browser in headless mode
        """
        self.logger.info(f"Opening browser")
        try:
            # Call the correct webdriver module. With this I can write a line for every browser ;)
            current_browser_name = getattr(webdriver, self._browser)
            if headless_mode and self._browser not in native_headless_browser:
                # call the "Options" module for the selected browser
                current_browser_options = globals()[self._browser + "Options"]()
                current_browser_options.headless = True
                self.logger.info(f"Browser {self._browser} set to headless")
                self.current_browser = current_browser_name(executable_path=self._webdriver[self._browser],
                                                            options=current_browser_options)
            else:
                self.current_browser = current_browser_name(executable_path=self._webdriver[self._browser])
            self.logger.info(f"{self._browser} opened correctly")

        except Exception as e:
            self.logger.error(f"Problems with the browser {self._browser}")
            self.logger.error(e)
            exit(1)

    def open_link(self):
        """
        Goes to the link taken from the config file
        """
        self.logger.info(f"{self._browser} is trying to open {self._web_page_link}")
        try:
            self.current_browser.get(self._web_page_link)
            self.logger.info(f"Now he's in the selected page where the title is: {self.current_browser.title}")
            print(f"Title before login: {self.current_browser.title}")
        except Exception as e:
            self.logger.error(f"Problem while opening the link {self._web_page_link}")
            self.logger.error(e)
            exit(1)

    def login(self):
        """
         Try to log into the web page. It inserts username, password and then click on the submit button.
         All those information came from the config file
        """
        self.logger.info(f"Starting to log in")
        if self.current_browser.title != self._logged_in_website_title:
            self.current_browser.maximize_window()
            self.logger.info("You're in the login page")
            # Fill input fields (or at least he try to...) and click the submit button
            try:
                # Fill username field
                username_input = self.current_browser.find_element_by_xpath(self._auth[USERNAME_TAG_XPATH])
                username_input.send_keys(self._auth[USERNAME_VALUE])
                self.logger.info("Username entered correctly")

                # If you don't want to write the secret password in an unsafe file, uncomment this portion
                # if self.auth["password_value"] == "":
                #     logger.info("Getting password from GUI")
                #     # current_password_value = password_with_gui()
                # else:
                #     logger.info("Getting password from the setting file")
                #     current_password_value = self._auth[PASSWORD_VALUE]

                # Fill password field
                current_password_value = self._auth[PASSWORD_VALUE]
                password_input = self.current_browser.find_element_by_xpath(self._auth[PASSWORD_TAG_XPATH])
                password_input.send_keys(current_password_value)
                self.logger.info("Password entered correctly")

                # Click submit button
                submit_button_input = self.current_browser.find_element_by_xpath(self._auth[SUBMIT_TAG_XPATH])
                submit_button_input.click()
                self.logger.info("Submit button clicked correctly")

                if not self.logged_in_check():
                    raise Exception("You're not logged in, there's a problem!")
            except Exception as e:
                self.logger.error("Problems during inputs filling")
                self.logger.error(e)
                self.current_browser.quit()
                self.logger.info("Quitted browser")
                exit(1)
        else:
            self.logger.info("Nice, you don't need to log in!")
            # self.current_browser.quit()
            # logger.info("Quitted browser")

    def logged_in_check(self) -> bool:
        """
        Check if you are logged into the site

        :return: True if you are logged in, False if not
        """
        self.logger.info(f"Checking if you are logged in")

        # if self.current_browser.title == self._logged_in_website_title:
        #     logger.info("Now you're logged in!")
        # else:
        #     logger.error("Wrong username or password. Please check them")
        #     self.current_browser.quit()
        #     exit(2)

        try:
            self.current_browser.find_element_by_xpath(self._auth[USERNAME_TAG_XPATH])
            self.logger.error(f"The username field is still there. You're not logged in dude")
            return False
        except:
            self.logger.info("Now you're logged in!")
            return True

    def do_refreshes(self, number_of_refreshes: list, refresh_page_sleep_time: list):
        """
        Refresh the pages a "number_of_refreshes" times waiting a "refresh_page_sleep_time" seconds.
        To try to fake a human-like interaction, those parameters are intervals and a random number between those are
        chosen

        :param number_of_refreshes: 2 element list, min and max number of refreshes
        :param refresh_page_sleep_time: 2 element list, min and max number of seconds to wait for the next refresh or action
        """
        number_of_refreshes = randint(number_of_refreshes[0], number_of_refreshes[1])
        sleep_time = randint(refresh_page_sleep_time[0], refresh_page_sleep_time[1])
        print(f"{number_of_refreshes} refresh selected. Waiting {sleep_time} seconds")
        self.logger.info(f"{number_of_refreshes} refresh selected. Waiting {sleep_time} seconds")
        time.sleep(sleep_time)
        while number_of_refreshes > 0:
            self.current_browser.refresh()
            # Scroll to the end of the page
            # self.current_browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            number_of_refreshes = number_of_refreshes - 1
            sleep_time = randint(refresh_page_sleep_time[0], refresh_page_sleep_time[1])
            self.logger.info(f"Refresh completed. You have {number_of_refreshes} other refreshes. "
                             f"Waiting {sleep_time} seconds")
            time.sleep(sleep_time)
        self.logger.info(f"Refresh completed")

    def check_changes(self, target_xpath: str, target_string: str) -> bool:
        """
        Check if there are changes in the page

        :param target_xpath: xpath of the resource
        :param target_string: string of the current text into the xpath. with site changes, this string will change too
        :return: True if there are changes, False instead
        """
        self.logger.info(f"Checking if there are changes")
        try:
            # if self.current_browser.title == self.logged_in_website_title:
            target = self.current_browser.find_element_by_xpath(target_xpath)
            print(f"Title after login: {self.current_browser.title}")
            print(f"Selected text: {target.text}")
            if target_string.strip() in target.text.strip():
                self.logger.info("Ancora non sono usciti")
                target_changed = False
            else:
                self.logger.info("AOH SO USCITIIIIIIII")
                target_changed = True
            return target_changed
            # else:
            #     logger.error(
            #         f"You're not logged in while you should, that's a problem dude. Maybe a different title of the page?")
        except Exception as e:
            self.logger.warning(f"Something went wrong while checking for the changes. Maybe there are results?")
            self.logger.warning(e)
            return True

    def logout(self, logout_xpaths: list):
        """
        Find the logout button from the xpaths and then click on it

        :param logout_xpaths: list of xpaths of the logout button. if it's hidden behind a select, put both xpaths into
        the list
        """
        self.logger.info("Logging out")
        for xpath in logout_xpaths:
            self.current_browser.find_element_by_xpath(xpath) \
                .click()
        # TODO: Add a condition to check you are really logged out
        self.logger.info("Logged out")

    def predefined_run(self):
        """
        Standard usage of this module. Open the browser, goes to the link, log into the site, refresh the page,
        check for changes, log out and close the browser.
        If changes are found, it does all those stuff again until the login with the browser in not-headless mode.
        Every information (browser, link, etc...) are located in config file
        """
        self.open_instance_of_browser(native_headless_browser=self._configuration[NATIVE_HEADLESS_BROWSER],
                                      headless_mode=self._configuration[HEADLESS])

        self.open_link()

        self.login()

        self.do_refreshes(self._configuration[NUMBER_OF_REFRESHES], self._configuration[REFRESH_PAGE_SLEEP_TIME])

        self.target_found = self.check_changes(self._configuration[TARGET_XPATH],
                                               self._configuration[TARGET_STRING])

        # List of stuff to click to logout
        logout_xpaths = self._configuration[LOGOUT_XPATHS]

        self.logout(logout_xpaths)

        self.current_browser.quit()

        if self.target_found:
            self.logger.info(f"Go son, go to check your results!")
            if self._browser not in self._configuration[NATIVE_HEADLESS_BROWSER]:
                self.open_instance_of_browser(native_headless_browser=self._configuration[NATIVE_HEADLESS_BROWSER])
                self.open_link()
                self.login()


if __name__ == "__main__":
    current_browser = SingleWindowBrowserScraper()
    current_browser.predefined_run()
