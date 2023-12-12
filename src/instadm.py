from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as CM
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from random import randint, uniform
from time import time, sleep
import random
import logging
import sqlite3

DEFAULT_IMPLICIT_WAIT = 1


class InstaDM(object):

    def __init__(self, username, password, headless=True, instapy_workspace=None, profileDir=None):
        self.selectors = {
            "accept_cookies": "//button[text()='Accept']",
            "home_to_login_button": "//button[text()='Log in']",
            "username_field": "username",
            "password_field": "password",
            "button_login": "//button/*[text()='Log in']",
            "login_check": "//*[@aria-label='Home'] | //button[text()='Save Info'] | //button[text()='Not Now']",
            "search_user": "queryBox",
            "select_user": '//div[text()="{}"]',
            "name": "((//div[@aria-labelledby]/div/span//img[@data-testid='user-avatar'])[1]//..//..//..//div[2]/div[2]/div)[1]",
            "next_button": "//button/*[text()='Next']",
            "textarea": "//div[@aria-label='Message' and @role='textbox']",
            "send": "//div[@role='button' and text()='Send']"
        }

        # Selenium config
        options = webdriver.ChromeOptions()

        if profileDir:
            options.add_argument("user-data-dir=profiles/" + profileDir)

        if headless:
            options.add_argument("--headless")

        mobile_emulation = {
            "userAgent": 'Mozilla/5.0 (Linux; Android 10.0; iPhone Xs Max Build/IML74K) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/91.0.4472.77 Mobile Safari/535.19'
        }
        options.add_experimental_option("mobileEmulation", mobile_emulation)
        options.add_argument("--log-level=3")

        self.driver = webdriver.Chrome(
            executable_path=CM().install(), options=options)
        self.driver.set_window_position(0, 0)
        self.driver.set_window_size(414, 936)

        # Instapy init DB
        self.instapy_workspace = instapy_workspace
        self.conn = None
        self.cursor = None
        if self.instapy_workspace is not None:
            self.conn = sqlite3.connect(
                self.instapy_workspace + "InstaPy/db/instapy.db")
            self.cursor = self.conn.cursor()

            cursor = self.conn.execute("""
                SELECT count(*)
                FROM sqlite_master
                WHERE type='table'
                AND name='message';
            """)
            count = cursor.fetchone()[0]

            if count == 0:
                self.conn.execute("""
                    CREATE TABLE "message" (
                        "username"    TEXT NOT NULL UNIQUE,
                        "message"    TEXT DEFAULT NULL,
                        "sent_message_at"    TIMESTAMP
                    );
                """)

        try:
            self.login(username, password)
        except Exception as e:
            logging.error(e)
            print(str(e))

    def login(self, username, password):
        self.driver.get('https://instagram.com/?hl=en')
        self.__random_sleep__(1, 3)

        # Check for splash screen
        try:
            login_div_xpath = "/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/article/div/div/div/div/div[2]/div[3]/button[1]/div"
            login_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, login_div_xpath))
            )
            login_div.click()
            self.__random_sleep__(1, 3)
        except TimeoutException:
            logging.info("No splash screen detected.")

        # Login process
        try:
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            self.__type_slow__(username_field, username)

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            self.__type_slow__(password_field, password)

            # Adjusted XPath for the actual login button
            login_button_xpath = "/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/main/article/div/div/div/div/div[2]/form/div[1]/div[6]/button"
            login_button = self.driver.find_element(By.XPATH, login_button_xpath)
            self.__click_element__(login_button)
            self.__random_sleep__(3, 5)
        except Exception as e:
            logging.error(f"Login failed: {e}")

    def click_if_element_exists(self, by, value, timeout=5):
        """Clicks an element if it exists within a specified timeout."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            return False

    def createCustomGreeting(self, greeting):
        # Get username and add custom greeting
        if self.__wait_for_element__(self.selectors['name'], "xpath", 10):
            user_name = self.__get_element__(
                self.selectors['name'], "xpath").text
            if user_name:
                greeting = greeting + " " + user_name + ", \n\n"
        else:
            greeting = greeting + ", \n\n"
        return greeting

    def typeMessage(self, user, message):
        # Check for 'Not Now' button and click it if present
        not_now_button_xpath = "//button[text()='Not Now']"  # Update this XPath as needed
        self.click_if_element_exists(By.XPATH, not_now_button_xpath)

        if self.__wait_for_element__(self.selectors['textarea'], "xpath"):
            message_box = self.__get_element__(self.selectors['textarea'], "xpath")
            message_box.click()
            self.__random_sleep__(1, 2)
            self.__type_slow__(message_box, message)

        if self.__wait_for_element__(self.selectors['send'], "xpath"):
            send_button = self.__get_element__(self.selectors['send'], "xpath")
            send_button.click()
            self.__random_sleep__(3, 5)
            print('Message sent successfully')
            self.__random_sleep__(2, 4)

    def sendMessage(self, user, message, greeting=None):
        logging.info(f'Send message to {user}')
        print(f'Send message to {user}')
        self.driver.get('https://www.instagram.com/direct/new/?hl=en')
        self.__random_sleep__(2, 4)

        try:
            # Type the username in the search box
            self.__wait_for_element__(self.selectors['search_user'], "name")
            search_box = self.__get_element__(self.selectors['search_user'], "name")
            self.__type_slow__(search_box, user)

            # Use the full XPath to select the first checkbox in the results list
            first_user_checkbox_xpath = "/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/div/div[2]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/div/div[3]/div/label/div/input"
            first_user_checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, first_user_checkbox_xpath))
            )
            first_user_checkbox.click()
            self.__random_sleep__(1, 3)

            # Use the new XPath to click the "Next" button
            next_button_xpath = "/html/body/div[2]/div/div/div[2]/div/div/div[1]/section/div/div[2]/div/div/div[1]/div[3]/div"
            next_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, next_button_xpath))
            )
            next_button.click()
            self.__random_sleep__()

            if greeting != None:
                greeting = self.createCustomGreeting(greeting)

            # Send message to the selected user
            if greeting != None:
                self.typeMessage(user, greeting + message)
            else:
                self.typeMessage(user, message)

            if self.conn is not None:
                self.cursor.execute(
                    'INSERT INTO message (username, message) VALUES(?, ?)', (user, message))
                self.conn.commit()
            self.__random_sleep__(5, 10)

            return True

        except Exception as e:
            logging.error(e)
            print(f'Error sending message to {user}: {e}')
            return False


    def sendGroupMessage(self, users, message):
        logging.info(f'Send group message to {users}')
        print(f'Send group message to {users}')
        self.driver.get('https://www.instagram.com/direct/new/?hl=en')
        self.__random_sleep__(5, 7)

        try:
            usersAndMessages = []
            for user in users:
                if self.conn is not None:
                    usersAndMessages.append((user, message))

                self.__wait_for_element__(
                    self.selectors['search_user'], "name")
                self.__type_slow__(self.selectors['search_user'], "name", user)
                self.__random_sleep__()

                # Select user from list
                elements = self.driver.find_elements_by_xpath(
                    self.selectors['select_user'].format(user))
                if elements and len(elements) > 0:
                    elements[0].click()
                    self.__random_sleep__()
                else:
                    print(f'User {user} not found! Skipping.')

            self.typeMessage(user, message)

            if self.conn is not None:
                self.cursor.executemany("""
                    INSERT OR IGNORE INTO message (username, message) VALUES(?, ?)
                """, usersAndMessages)
                self.conn.commit()
            self.__random_sleep__(50, 60)

            return True

        except Exception as e:
            logging.error(e)
            return False

    def sendGroupIDMessage(self, chatID, message):
        logging.info(f'Send group message to {chatID}')
        print(f'Send group message to {chatID}')
        self.driver.get('https://www.instagram.com/direct/inbox/')
        self.__random_sleep__(5, 7)

        # Definitely a better way to do this:
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB*2 + Keys.ENTER).perform()
        actions.send_keys(Keys.TAB*4 + Keys.ENTER).perform()

        if self.__wait_for_element__(f"//a[@href='/direct/t/{chatID}']", 'xpath', 10):
            self.__get_element__(
                f"//a[@href='/direct/t/{chatID}']", 'xpath').click()
            self.__random_sleep__(3, 5)

        try:
            usersAndMessages = [chatID]

            if self.__wait_for_element__(self.selectors['textarea'], "xpath"):
                self.__type_slow__(
                    self.selectors['textarea'], "xpath", message)
                self.__random_sleep__()

            if self.__wait_for_element__(self.selectors['send'], "xpath"):
                self.__get_element__(self.selectors['send'], "xpath").click()
                self.__random_sleep__(3, 5)
                print('Message sent successfully')

            if self.conn is not None:
                self.cursor.executemany("""
                    INSERT OR IGNORE INTO message (username, message) VALUES(?, ?)
                """, usersAndMessages)
                self.conn.commit()
            self.__random_sleep__(50, 60)

            return True

        except Exception as e:
            logging.error(e)
            return False

    def __get_element__(self, element_tag, locator):
        """Wait for element and then return when it is available"""
        try:
            locator = locator.upper()
            dr = self.driver
            if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_id(element_tag))
            elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_name(element_tag))
            elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_xpath(element_tag))
            elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTOR, element_tag):
                return WebDriverWait(dr, 15).until(lambda d: dr.find_element_by_css_selector(element_tag))
            else:
                logging.info(f"Error: Incorrect locator = {locator}")
        except Exception as e:
            logging.error(e)
        logging.info(f"Element not found with {locator} : {element_tag}")
        return None

    def is_element_present(self, how, what):
        """Check if an element is present"""
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException:
            return False
        return True

    def __wait_for_element__(self, element_tag, locator, timeout=30):
        """Wait till element present. Max 30 seconds"""
        result = False
        self.driver.implicitly_wait(0)
        locator = locator.upper()
        for i in range(timeout):
            initTime = time()
            try:
                if locator == 'ID' and self.is_element_present(By.ID, element_tag):
                    result = True
                    break
                elif locator == 'NAME' and self.is_element_present(By.NAME, element_tag):
                    result = True
                    break
                elif locator == 'XPATH' and self.is_element_present(By.XPATH, element_tag):
                    result = True
                    break
                elif locator == 'CSS' and self.is_element_present(By.CSS_SELECTORS, element_tag):
                    result = True
                    break
                else:
                    logging.info(f"Error: Incorrect locator = {locator}")
            except Exception as e:
                logging.error(e)
                print(f"Exception when __wait_for_element__ : {e}")

            sleep(1 - (time() - initTime))
        else:
            print(
                f"Timed out. Element not found with {locator} : {element_tag}")
        self.driver.implicitly_wait(DEFAULT_IMPLICIT_WAIT)
        return result

    def __type_slow__(self, element, text):
        if element:
            for character in text:
                element.send_keys(character)
                sleep(random.uniform(0.1, 0.3))  # Delay between key presses

    def __random_sleep__(self, min_sleep=1, max_sleep=3):
        sleep_time = random.uniform(min_sleep, max_sleep)
        sleep(sleep_time)


    def __scrolldown__(self):
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

    def teardown(self):
        self.__random_sleep__(1, 3)
        self.driver.close()
        self.driver.quit()

    def __click_element__(self, element):
        try:
            # Scroll into view and click the element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.__random_sleep__(0.5, 1.5)
            element.click()
        except Exception as e:
            logging.error(f"Error clicking element: {e}")
            # Attempting JavaScript click as a fallback
            self.driver.execute_script("arguments[0].click();", element)
    
    def __random_scroll__(self):
        scroll_command = "window.scrollBy(0, arguments[0]);"
        scroll_value = random.randint(-300, 300)  # Scroll up or down randomly
        self.driver.execute_script(scroll_command, scroll_value)

    def __click_random_element__(self, elements):
        if elements:
            random_element = random.choice(elements)
            self.__click_element__(random_element)
