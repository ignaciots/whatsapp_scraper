import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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


# Scroll and find media
def scrape_media(driver):
    last_height = 0

    while True:
        try:
            # Wait for video elements to load dynamically
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class, 'message-in')]//video"))
            )
        except Exception as e:
            print("Timeout waiting for video elements. Continuing...")
            break

        # Locate video elements
        media_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'message-in')]//video")
        print(f"Found {len(media_elements)} video elements.")
        for media in media_elements:
            src = media.get_attribute("src")
            if src and "blob:" not in src:
                save_media_blob(driver, src)

        # Scroll up to load more content
        driver.execute_script("window.scrollTo(0, 0);")
        random_delay()

        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No more content to load.")
            break
        last_height = new_height



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
