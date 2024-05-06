import sys
from typing import Tuple
from time import sleep
from datetime import time, datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from joblib import Parallel, delayed
import pytz  # Tambahkan impor modul pytz

# params
booking_site_url = 'https://id-mpl.com/ticket'
begin_time = time(0, 0)
end_time = time(18,0 )
max_try = 500
# reservation_time and reservation_name are given as arguments when python script runs
reservation_time = int(sys.argv[1])
reservation_name = sys.argv[2]

options = webdriver.ChromeOptions()
# comment out this line to see the process in chrome
service = Service(executable_path=r"C:\Users\USER\Documents\chromedriver-win64\chromedriver.exe")
options.add_argument('--headless')
driver = webdriver.Chrome(service=service, options=options)

# Tentukan zona waktu 'Asia/Jakarta'
jkt_timezone = pytz.timezone('Asia/Jakarta')

def check_current_time(begin_time: time, end_time: time) -> Tuple[time, bool]:
    '''
    Check current time is between 00:00 and 00:15. 
    Returns current time and if it is between begin and end time.
    '''
    # Tambahkan konversi zona waktu ke 'Asia/Jakarta'
    dt_now = datetime.now(jkt_timezone)
    current_time = time(dt_now.hour, dt_now.minute, dt_now.second)
    return current_time, (begin_time <= current_time) and (current_time < end_time)


def make_a_reservation(reservation_time:int, reservation_name:str) -> bool:
    '''
    Make a reservation for the given time and name at the booking site.
    Return the status if the reservation is made successfully or not.
    '''
    try:
        print("Step 1: Opening booking site...")
        driver.get(booking_site_url)
        print("Step 1: Successfully opened booking site.")

        print("Step 2: Clicking on the 'WATCH' button...")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@class="button button-watch button-ticket m-0 mb-1"]'))).click()
        print("Step 2: Successfully clicked on the 'WATCH' button.")

        # Wait for the new URL to load
        WebDriverWait(driver, 10).until(EC.url_contains("mplid.cognitix.id"))

        print("Step 3: Clicking on the 'BUY TICKET' button...")
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="ticket-box block type-a"]/a[@class="btn-pill block"]'))).click()
        print("Step 3: Successfully clicked on the 'BUY TICKET' button.")

        # Find the dropdown element
        dropdown_element = driver.find_element_by_css_selector('select.select-process-form')

        print("Step 4: Selecting option '2' from the dropdown...")
        Select(dropdown_element).select_by_value('2')
        print("Step 4: Successfully selected option '2' from the dropdown.")

        # Fill in the Full Name
        full_name_input = driver.find_element_by_id('customer_fullname')
        full_name_input.clear()
        full_name_input.send_keys('Amura Maulidi Fachry')

        # Fill in the Email
        email_input = driver.find_element_by_id('customer_email')
        email_input.clear()
        email_input.send_keys('edogawaconax@gmail.com')

        # Fill in the Phone Number
        phone_input = driver.find_element_by_id('customer_phone')
        phone_input.clear()
        phone_input.send_keys('0899510731')

        # press submit button
        order_button = driver.find_element_by_css_selector('button.btn-pill.btn-submit-registrants.block')
        order_button.click()
        print("Step 5: Submitted the form successfully.")

        payment_method_section = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'section.pick-payment-method')))

        # Click on the radio button for E-Wallet DANA
        dana_radio_button = payment_method_section.find_element_by_css_selector('input[data-toggle-payment="payment-dana"]')
        dana_radio_button.click()
        print("Step 6: Selected payment method DANA successfully.")

        # Click on the "PROCESS PAYMENT" button
        process_payment_button = driver.find_element_by_css_selector('button.btn-pill.btn-process-payment.block')
        process_payment_button.click()
        print("Step 7: Clicked on the 'PROCESS PAYMENT' button.")

        # Wait for a few seconds to ensure the next page is fully loaded
        time.sleep(5)  # Adjust according to the speed of page opening

        # Get all active window handles
        handles = driver.window_handles

        # Assume the new window is the last opened window
        new_window_handle = handles[-1]

        # Switch to the new window
        driver.switch_to.window(new_window_handle)
        print("Step 8: Switched to the new window successfully.")
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        # Close the driver
        driver.quit()


def try_booking(reservation_time:int, reservation_name:str, max_try:int=1000) -> None:
    '''
    Try booking a reservation until either one reservation is made successfully or the attempt time reaches the max_try
    '''
    # initialize the params
    current_time, is_during_running_time = check_current_time(begin_time, end_time)
    reservation_completed = False
    try_num = 1

    # repreat booking a reservation every second
    while True:
        if not is_during_running_time:
            print(f'Not Running the program. It is {current_time} and not between {begin_time} and {end_time}')

            # sleep less as the time gets close to the begin_time
            if current_time >= time(23,59,59):
                sleep(0.001)
            elif time(23,59,58) <= current_time < time(23,59,59):
                sleep(0.5)
            else:
                sleep(1)

            try_num += 1
            current_time, is_during_running_time = check_current_time(begin_time, end_time)
            continue

        print(f'----- try : {try_num} -----')
        # try to get ticket
        reservation_completed = make_a_reservation(reservation_time, reservation_name)

        if reservation_completed:
            print('Got a ticket!!')
            break
        elif try_num == max_try:
            print(f'Tried {try_num} times, but couldn\'t get tickets..')
            break
        else:
            sleep(1)
            try_num += 1
            current_time, is_during_running_time = check_current_time(begin_time, end_time)

if __name__ == '__main__':
    current_time, _ = check_current_time(begin_time, end_time)
    reservation_datetime = datetime.combine(datetime.now(), time(reservation_time // 100, reservation_time % 100))

    # Periksa apakah waktu saat ini sudah mencapai atau melebihi waktu reservasi yang ditentukan
    if current_time >= reservation_datetime.time():
        try_booking(reservation_time, reservation_name, max_try)
    else:
        print(f"Waktu reservasi adalah {reservation_datetime.time()}, sedangkan waktu saat ini adalah {current_time}. Menunggu hingga waktu reservasi...")
        sleep((reservation_datetime - datetime.now()).total_seconds())
        try_booking(reservation_time, reservation_name, max_try)
