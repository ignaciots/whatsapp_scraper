import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Configure folder to save media
SAVE_FOLDER = "WhatsappMedia"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Configure the WhatsApp Group Name
GROUP_NAME = "familia!"

# Initialize Selenium WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=./whatsapp_data")  # Keeps your session logged in
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Open WhatsApp Web and navigate to the group
def open_whatsapp(driver):
    driver.get("https://web.whatsapp.com/")
    print("Scan the QR code if not already logged in.")
    time.sleep(15)  # Wait for the session to load

    # Search for the group
    search_box = driver.find_element(By.XPATH, "//div[@title='Search input textbox']")
    search_box.click()
    search_box.send_keys(GROUP_NAME)
    search_box.send_keys(Keys.ENTER)

# Download all media from the group
def download_media(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    print("Scrolling through the chat...")
    
    while True:
        media_elements = driver.find_elements(By.XPATH, "//img[contains(@src, 'blob:')] | //video[contains(@src, 'blob:')]")
        
        for media in media_elements:
            src = media.get_attribute("src")
            media_type = "image" if "image" in src else "video"
            download_media_from_src(src, media_type)
        
        # Scroll up to load older messages
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(3)  # Wait for content to load
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break
        last_height = new_height

def download_media_from_src(src, media_type):
    # Save media files locally
    import requests
    from urllib.parse import urlparse
    
    file_extension = ".jpg" if media_type == "image" else ".mp4"
    filename = os.path.basename(urlparse(src).path) + file_extension
    filepath = os.path.join(SAVE_FOLDER, filename)
    
    if not os.path.exists(filepath):
        print(f"Downloading {media_type}: {filename}")
        response = requests.get(src)
        with open(filepath, "wb") as file:
            file.write(response.content)
    else:
        print(f"Already downloaded: {filename}")

# Main function
def main():
    driver = init_driver()
    try:
        open_whatsapp(driver)
        download_media(driver)
    finally:
        driver.quit()
        print(f"All media saved to: {SAVE_FOLDER}")

if __name__ == "__main__":
    main()
