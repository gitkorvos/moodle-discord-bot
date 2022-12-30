from selenium import webdriver
from selenium.webdriver.common.by import By
import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import json
import re
import os


from selenium.webdriver.edge.options import Options

import sqlite3

edge_options = Options()
edge_options.add_argument("--headless")

from datetime import datetime, timedelta

# Breakpoint for when selenium should be used to refresh the cached data
HOURS_BETWEEN_CACHE = 3

# TESTING ONLY
def connect_to_database():
    database_exists = False

    if os.path.exists("data.db"):
        database_exists = True

    connection = sqlite3.connect("data.db")

    # Create the tables if the database is being created for the first time
    if not database_exists:
        database_cursor = connection.cursor()

        database_cursor.executescript('''
            CREATE TABLE accounts (
                discord_id TEXT PRIMARY KEY,
                username TEXT,
                password TEXT
            );
            
            CREATE TABLE events (
                username TEXT PRIMARY KEY,
                last_updated TEXT,
                data TEXT
            );
        ''')

        connection.commit()
        database_cursor.close()
    
    return connection

def get_cached_moodle_data(login_username, data_table):

    database_connection = connect_to_database()

    database_cursor = database_connection.cursor()
    database_cursor.execute(f"SELECT username, last_updated, data FROM {data_table} WHERE username = '{login_username}'")

    cached_data = database_cursor.fetchone()    

    if not cached_data:
        return False

    if datetime.now() - datetime.strptime(cached_data[1], '%Y-%m-%d %H:%M:%S.%f') > timedelta(hours=HOURS_BETWEEN_CACHE):
        return False

    return json.loads(cached_data[2]) # RETURN THE DATA

def cache_moodle_data(login_username, data_table, json_data):

    database_connection = connect_to_database()

    SQL_QUERY_CACHE = f'INSERT INTO {data_table} (username, last_updated, data) VALUES (?, ?, ?) ON CONFLICT (username) DO UPDATE SET last_updated = EXCLUDED.last_updated, data = EXCLUDED.data'

    jsonified_data = json.dumps(json_data)
    database_cursor = database_connection.cursor()
    database_cursor.execute(SQL_QUERY_CACHE, (login_username, datetime.now(), jsonified_data))
    database_connection.commit()

def authenticate_driver(login_username: str = "", login_password: str = ""):

    driver = webdriver.Edge(options=edge_options)

    if len(login_password) == 0 or len(login_username) == 0:
        raise Exception("Please provide valid 'username' and 'password' parameters")
    
    driver.get("https://moodle.port.ac.uk/login/index.php")
    driver.find_element(By.ID, 'username').send_keys(login_username)
    driver.find_element(By.ID, 'password').send_keys(login_password)
    
    try:
        driver.find_element(By.ID, 'loginbtn').click()

    except:
        print("authenticate_driver: failed to login")

    return driver

def get_events_data(login_username, login_password):

    events = []

    previous_data = get_cached_moodle_data(login_username, "events")

    if previous_data:
        return previous_data

    driver = authenticate_driver(login_username, login_password)

    wait = WebDriverWait(driver, 10)
    events_show_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-action="more-events"]')))
    events_show_button.click()

    wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '[data-action="more-events"]')))
    time.sleep(1)

    deadline_events = driver.find_elements(By.CLASS_NAME, 'timeline-event-list-item')

    for event in deadline_events:

        event_dict = {}

        a_href = event.find_element(By.TAG_NAME, 'a')
        event_data = a_href.get_attribute('aria-label')

        event_name = event_data.split('activity')[0]
        due_date = event_data.split('due on')[1]

        module_details = re.search(r'activity in (.*) is due on', event_data).group(1)

        module_pattern = r'M[0-9]{5}-20[0-9]{2}/[0-9]{2}-(SMSEP|SMYEAR)'

        module_codes = []

        module_code_matches = re.finditer(module_pattern, module_details)
        for match in module_code_matches:
            module_codes.append(match.group(0))

        module_name = re.sub(module_pattern, "", module_details)

        event_dict['event_title'] = event_name

        event_dict['event_codes'] = ", ".join(module_codes)
        event_dict['event_name'] = module_name.replace(",", "")

        event_dict['due_date'] = due_date

        events.append(event_dict)

    cache_moodle_data(login_username, "events", events)
    return events

def get_account(discord_id):

    database_connection = connect_to_database()
    database_cursor = database_connection.cursor()

    database_cursor.execute(f"SELECT discord_id, username, password FROM accounts WHERE discord_id = '{discord_id}'")

    cached_data = database_cursor.fetchone()

    if not cached_data:
        return False

    return cached_data

def register_account(discord_id, username, password):

    database_connection = connect_to_database()

    SQL_QUERY_CACHE = f'INSERT INTO accounts (discord_id, username, password) VALUES (?, ?, ?) ON CONFLICT (discord_id) DO UPDATE SET username = EXCLUDED.username, password = EXCLUDED.password'

    database_cursor = database_connection.cursor()
    database_cursor.execute(SQL_QUERY_CACHE, (discord_id, username, password))
    database_connection.commit()

