import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Constants
SAVE_FOLDER = "WhatsAppMedia"
GROUP_NAME = "familia!"  # Replace with your group name
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Random delay to mimic human behavior
def random_delay():
    time.sleep(random.uniform(2, 5))

# Initialize the WebDriver with headless mode and random user-agent
def init_driver():
    user_agent = random.choice(USER_AGENTS)
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    # Add session persistence
    chrome_options.add_argument("--user-data-dir=./whatsapp_session")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Log in to WhatsApp Web
def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    print("Please scan the QR code if prompted.")
    try:
        # Wait until the main WhatsApp UI is loaded
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']"))
        )
        print("Login successful.")
    except Exception as e:
        print("Login timeout. Please try again.")


# Navigate to the specified group
def navigate_to_group(driver):
    try:
        # Wait for the search box to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-tab='3']"))
        )
        search_box = driver.find_element(By.XPATH, "//div[@contenteditable='true' and @data-tab='3']")
        search_box.click()
        random_delay()
        search_box.send_keys(GROUP_NAME)
        random_delay()
        search_box.send_keys(Keys.ENTER)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, f"//span[@title='{GROUP_NAME}']"))
        )
        print(f"Successfully navigated to group: {GROUP_NAME}")
    except Exception as e:
        print(f"Failed to navigate to group: {e}")

def scrape_media(driver):
    all_videos_downloaded = False
    downloaded_videos = set()  # Keep track of downloaded videos
    retries = 10  # Limit the number of scroll attempts to prevent infinite loops

    last_known_scroll_height = driver.execute_script("return document.body.scrollHeight")

    while not all_videos_downloaded and retries > 0:
        try:
            # Locate the chat window dynamically
            print("Attempting to locate chat window...")
            chat_window = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@data-tab, '8')]"))
            )
            print("Chat window located. Scrolling...")
            
            # Capture current scroll position
            current_scroll_position = driver.execute_script("return arguments[0].scrollTop;", chat_window)
            print(f"Current scroll position before scroll: {current_scroll_position}")
            
            # Scroll up
            chat_window.click()
            chat_window.send_keys(Keys.PAGE_UP)
            
            # Wait for scrollTop to decrease (scrolling action)
            WebDriverWait(driver, 20).until(
                lambda d: driver.execute_script("return arguments[0].scrollTop;", chat_window) < current_scroll_position
            )
            print(f"Current scroll position after scroll: {driver.execute_script('return arguments[0].scrollTop;', chat_window)}")

            # Wait for new content to load (scrollHeight to increase)
            WebDriverWait(driver, 20).until(
                lambda d: driver.execute_script("return document.body.scrollHeight") > last_known_scroll_height
            )
            last_known_scroll_height = driver.execute_script("return document.body.scrollHeight")
            print(f"Scroll height after loading new content: {last_known_scroll_height}")

        except TimeoutException:
            print("No new content loaded. Stopping scroll.")
            all_videos_downloaded = True
            continue

        # Locate media elements
        media_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]//img[contains(@src, 'blob:')]")
        print(f"Total media elements found: {len(media_elements)}")

        # Save media if not already downloaded
        for media in media_elements:
            src = media.get_attribute("src")
            if src and "blob:" not in src and src not in downloaded_videos:
                save_media_blob(driver, src)
                downloaded_videos.add(src)

        retries -= 1

    print("Finished scrolling and scraping media.")



# Save video media blobs
def save_media_blob(driver, src):
    file_name = f"{time.time_ns()}.mp4"
    file_path = os.path.join(SAVE_FOLDER, file_name)

    try:
        response = requests.get(src)
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"Video saved: {file_path}")
    except Exception as e:
        print(f"Error saving video: {e}")


# Main function
def main():
    driver = init_driver()
    try:
        open_whatsapp(driver)
        navigate_to_group(driver)
        scrape_media(driver)
    finally:
        driver.quit()
        print(f"All media saved to: {SAVE_FOLDER}")

if __name__ == "__main__":
    main()
