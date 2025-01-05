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

SCROLL_RETRIES = 1
SAVE_FOLDER = "WhatsAppMedia"
GROUP_NAME = "familia!"  
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]
os.makedirs(SAVE_FOLDER, exist_ok=True)


def random_delay():
    time.sleep(random.uniform(2, 5))


def init_driver():
    user_agent = random.choice(USER_AGENTS)
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-data-dir=./whatsapp_session")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-download-notification")
    chrome_options.add_experimental_option("prefs", {
        "download.prompt_for_download": False,
        "profile.default_content_settings.popups": 0,
        "download.default_directory": f"{os.path.abspath(SAVE_FOLDER)}",
        "download.directory_upgrade": True
        })
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    print("Please scan the QR code if prompted.")
    try:
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']"))
        )
        print("Login successful.")
    except Exception as e:
        print(f"Login timeout. Please try again. \n {e}")


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


def scrape_videos(driver):
    try:
        WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@data-tab, '8')]"))
            )
        print("Chat window located, locating group details")
        group_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id=\"main\"]/header/div[1]"))
                    )
        group_button.click()
        time.sleep(2)
        print("Group Profile Button clicked successfully!")
        media_section_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id=\"app\"]/div/div[3]/div/div[5]/span/div/span/div/div/div/section/div[3]/div[1]"))
                    )
        media_section_button.click()
        time.sleep(5)
        print("Media Section button clicked succesfully!")

        download_buttons = []
        possible_xpaths = [
                "//button[@tabindex and span[@data-icon='media-download']]"
                ]
        for xpath in possible_xpaths:
            download_buttons.extend(driver.find_elements(By.XPATH, xpath))
            if download_buttons:
                break
        if not download_buttons:
            print("No download buttons found with any of the specified XPaths.")
            return  
        print(f'Number of video thumbnail buttons: {len(download_buttons)}')

        for button in download_buttons:
            print(f"Clicking thumbnail download button {download_buttons.index(button)}")
            try:
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
            except TimeoutException:
                print("Failed to locate video download thumbnail after click. Moving to next video.")
            except Exception as e:
                print(f"An error occurred while clicking video download thumbnail: {e}")

        video_thumbnails = driver.find_elements(By.XPATH, "//div[contains(@style, 'background-image: url(\"data:image/jpeg;base64,')]")

        for thumbnail in video_thumbnails:
            try:
                driver.execute_script("arguments[0].click();", thumbnail)
                time.sleep(2)

                # Look for the video element that might appear after clicking
                video_element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "video"))
                )
                downloaded_videos = set() 
                src = video_element.get_attribute('src')
                if src and src.startswith('blob:') and src not in downloaded_videos:
                    save_media_blob(driver, src)
                    downloaded_videos.add(src)

                    print(f"Video URL found: {src}")
                    # Implement your download logic with requests

            except TimeoutException:
                print("No video element found after clicking thumbnail.")
            except Exception as e:
                print(f"An error occurred: {e}")

    except TimeoutException as e:
        print(f"Timeout occurred while waiting for elements: {e}")


def scroll_chat(driver):
    
    while SCROLL_RETRIES > 0:
        try:
            print(f'retry number: {SCROLL_RETRIES}')
            chat_window = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@data-tab, '8')]"))
            )
            print("Main Chat window located, scrolling")

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
                    button.click()
                    print("Button clicked successfully!")
                    break
                last_known_scroll_height = new_height
                print(f"Scroll height AFTER scroll: {last_known_scroll_height}")

        except TimeoutException:
            print("Timeout occurred while waiting for elements.")
        except NoSuchElementException:
            print("No more chat history was found.")
        SCROLL_RETRIES -= 1
    print("Finished scrolling for older messages.")

def save_media_blob(driver, src, save_folder=SAVE_FOLDER):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    file_name = f"{time.time_ns()}.mp4"
    file_path = os.path.join(save_folder, file_name)

    if src.startswith('blob:'):
        # For blob URLs, we need to use JavaScript to trigger a download
        js_code = """
            var a = document.createElement('a');
            a.href = arguments[0];
            a.download = arguments[1];
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        """
        driver.execute_script(js_code, src, file_name)
        print(f"Download initiated for: {file_path}. Check your default download directory.")
    else:
        # This part is for regular HTTP URLs, which you can keep if needed
        try:
            import requests
            response = requests.get(src, stream=True)
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print(f"Video saved: {file_path}")
        except Exception as e:
            print(f"Error saving video from URL {src}: {e}")


def main():
    driver = init_driver()
    try:
        open_whatsapp(driver)
        navigate_to_group(driver)
        scroll_chat(driver)
        scrape_videos(driver)
    finally:
        driver.quit()
        print(f"All media was saved to: {SAVE_FOLDER}")

if __name__ == "__main__":
    main()