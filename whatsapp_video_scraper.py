import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests

# Constants
SAVE_FOLDER = "WhatsAppMedia"
GROUP_NAME = "familia!"  
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
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-data-dir=./whatsapp_session")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Log in to WhatsApp Web
def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    print("Please scan the QR code if prompted.")
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']"))
        )
        print("Login successful.")
    except Exception as e:
        print("Login timeout. Please try again.")

# Navigate to the specified group
def navigate_to_group(driver):
    try:
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
    downloaded_videos = set()  
    retries = 1 
    while not all_videos_downloaded and retries > 0:
        try:
            print(f'retry number: {retries}')
            chat_window = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@data-tab, '8')]"))
            )
            print("Chat window located, scrolling")

            last_known_scroll_height = driver.execute_script("return arguments[0].scrollHeight;", chat_window)
            while True:
                print(f"Scroll height BEFORE scroll: {last_known_scroll_height}")
                driver.execute_script("arguments[0].scrollIntoView(true);", chat_window)
                time.sleep(5)  
                new_height = driver.execute_script("return arguments[0].scrollHeight;", chat_window)
                if new_height == last_known_scroll_height:
                    button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[.//div[text()='Click here to get older messages from your phone.']]"))
                    )
                    #button.click()
                    #print("Button clicked successfully!")
                    continue
                last_known_scroll_height = new_height
                print(f"Scroll height AFTER scroll: {last_known_scroll_height}")

            download_buttons = driver.find_elements(By.XPATH, "//div/button[span[svg[path[@d]]]]")
            print(f'Number of video buttons: {len(download_buttons)}')
            new_videos = False
            for button in download_buttons:
                try:
                    # Click the download button (assuming it's the only nested SVG with path inside)
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(5)  # Wait for the video to become visible

                    # Find the video element after clicking (look for img with src attribute directly under a div with role attribute)
                    video_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='button']//img[@src]"))
                    )
                    src = video_element.get_attribute('src')
                    if src and src.startswith('blob:') and src not in downloaded_videos:
                        save_media_blob(src)
                        downloaded_videos.add(src)
                        new_videos = True
                    if not new_videos:
                        all_videos_downloaded = True
                    else:
                        retries = 1
                except TimeoutException:
                    print("Failed to locate video after click. Moving to next video.")
                except Exception as e:
                    print(f"An error occurred while downloading video: {e}")

        except TimeoutException:
            print("Timeout occurred while waiting for elements.")
        except NoSuchElementException:
            print("No more elements found.")
        retries -= 1
    print("Finished scrolling and scraping media.")

# Save video media
def save_media_blob(src):
    file_name = f"{time.time_ns()}.mp4"
    file_path = os.path.join(SAVE_FOLDER, file_name)

    try:
        response = requests.get(src, stream=True)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
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