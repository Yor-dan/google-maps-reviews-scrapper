import threading
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import pandas as pd

# CONFIG VARIABLES
GOOGLE_MAPS_URL = "https://www.google.com/maps"
MAPS_LANGUAGE = "id"
PLACE_NAME = "Tebet Eco Park" # <- Set the place name
MORE_BUTTON_TEXT = "Lainnya"
REVIEWS_LIMIT = 8000
OUTPUT_FILE = "result.xlsx"

stop_event = threading.Event()

def progress_logger(seconds: int, items: list[str], stop: threading.Event) -> None:
    start_time = time.time()

    while not stop.is_set():
        time.sleep(seconds)
        elapsed = int((time.time() - start_time) / 60)
        print(f"⏱️ {elapsed} minutes elapsed - {len(items)} reviews scraped.")

def main() -> None:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # options.add_argument('--headless=new')
    options.add_argument('--disable-images')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Disable image loading in Chrome
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)

    print("🚀 Starting Chrome Driver...")
    driver = webdriver.Chrome(options=options)

    reviews_texts: list[str] = []

    try:
        print(f"📍 Navigating to: {GOOGLE_MAPS_URL}")
        driver.get(f"{GOOGLE_MAPS_URL}?hl={MAPS_LANGUAGE}")
        time.sleep(3)

        # Type the place name in the search box
        search_box = driver.find_element(By.ID, "ucc-1")
        search_box.send_keys(PLACE_NAME)
        search_box.send_keys(Keys.RETURN)
        time.sleep(3)

        # Open the reviews section
        reviews_button = driver.find_element("xpath", f"//*[@aria-label='Ulasan untuk {PLACE_NAME}']")
        reviews_button.click()
        time.sleep(3)

        # Start progress logger thread
        logger_thread = threading.Thread(target=progress_logger, args=(300, reviews_texts, stop_event))
        logger_thread.start()

        while len(reviews_texts) < REVIEWS_LIMIT:
            reviews_elements = driver.find_elements(By.CLASS_NAME, "jftiEf")

            # checkpoint
            if len(reviews_elements) >= 100 :
                # click "See more" buttons
                more_buttons = driver.find_elements(By.XPATH, f"//button[text()='{MORE_BUTTON_TEXT}']")
                for button in more_buttons:
                    button.click()

                review_text_elements = driver.find_elements(By.CLASS_NAME, "wiI7pd")
                reviews_texts += [r.text.replace('\n', ' ') for r in review_text_elements[:-1]]

                first_elements_to_delete = driver.find_elements(By.CLASS_NAME, "AyRUI")
                for element in first_elements_to_delete[:-1]:
                    driver.execute_script("""
                        const element = arguments[0];
                        element.parentNode.removeChild(element);
                    """, element)

                second_elements_to_delete = driver.find_elements(By.CLASS_NAME, "TFQHme")
                for element in second_elements_to_delete[:-1]:
                    driver.execute_script("""
                        const element = arguments[0];
                        element.parentNode.removeChild(element);
                    """, element)

                for element in reviews_elements[:-1]:
                    driver.execute_script("""
                        const element = arguments[0];
                        element.parentNode.removeChild(element);
                    """, element)

            # scroll to load reviews
            scroll_div = driver.find_element("css selector", 'div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde')
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_div)
            time.sleep(3)

    finally:
        stop_event.set()
        print("🛑 Logger thread stopped.")

        df = pd.DataFrame(reviews_texts, columns=["text"])
        df.to_excel(OUTPUT_FILE, index=False)

        print(f"✅ Scraped {len(reviews_texts)} reviews.")

        print("🔒 Closing the driver...")
        driver.quit()

if __name__ == "__main__":
    main()