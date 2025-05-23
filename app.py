from flask import Flask, jsonify, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import subprocess
import os
import time
import logging
import base64
import uuid
import traceback
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

TEMP_IMAGE_DIR = "temp_images"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)

ADMIN_CODE = "ICU14CU"

chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
chromedriver_bin = os.environ.get("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"

options = Options()
options.binary_location = chrome_bin
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument(f"user-agent={user_agent}")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")

service = Service(chromedriver_bin)
driver = webdriver.Chrome(service=service, options=options)
logged_in = False

def login_once(email, password):
    global logged_in
    if not logged_in:
        login_to_bing(driver, email, password)
        logged_in = True

def take_screenshot_in_memory(driver):
    screenshot_png = driver.get_screenshot_as_png()
    logging.info("📸 Screenshot captured in memory.")
    return screenshot_png

def login_to_bing(driver, email, password):
    try:
        logging.info("🔗 Navigating to Bing login page...")
        driver.get("https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3a%2f%2fwww.bing.com%2fimages%2fcreate%3fsude%3d1&cobrandid=03f1ec5e-1843-43e5-a2f6-e60a6e0b1b9b")
        time.sleep(3)
        logging.info("✅ Login page loaded.")
        take_screenshot_in_memory(driver)
        time.sleep(3)

        logging.info("📧 Entering email...")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "usernameEntry")))
        driver.find_element(By.ID, "usernameEntry").send_keys(email)
        logging.info("✅ Email entered.")
        driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
        logging.info("🖱️ Clicked next after email.")
        time.sleep(3)
        take_screenshot_in_memory(driver)

        logging.info("🔑 Using password login...")
        try:
            # Wait up to 15 seconds for the "Use your password" button
            use_pwd_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Use your password']"))
            )
            use_pwd_btn.click()
            logging.info("🖱️ Clicked 'Use your password'.")
            time.sleep(2)
            take_screenshot_in_memory(driver)
        except TimeoutException:
            logging.info("'Use your password' button not found after 15 seconds. Proceeding to password entry.")

        logging.info("🔒 Entering password...")
        driver.find_element(By.ID, "passwordEntry").send_keys(password)
        logging.info("✅ Password entered.")
        driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
        logging.info("🖱️ Clicked next after password.")
        time.sleep(3)
        take_screenshot_in_memory(driver)

        logging.info("✅ Staying signed in...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='primaryButton']"))
        ).click()
        logging.info("🖱️ Clicked 'Stay signed in'.")
        logging.info("===Navigated To Main Page===")
        driver.get("https://bing.com/images/create")
        WebDriverWait(driver, 20).until(
           EC.presence_of_element_located((By.ID, "sb_form_q"))
        )
        take_screenshot_in_memory(driver)
    except Exception as e:
        logging.error(f"❌ Login failed: {e}")
        take_screenshot_in_memory(driver)
        raise
        
def generate_images(driver, prompt):
    logging.info("🖊️ Typing prompt...")
    textarea = driver.find_element(By.ID, "sb_form_q")
    textarea.clear()
    textarea.send_keys(prompt)
    logging.info("✅ Prompt typed.")

    button = driver.find_element(By.ID, "create_btn_c")
    driver.execute_script("arguments[0].click();", button)
    logging.info("🖱️ Clicked 'Create' button.")

    # Poll for images instead of fixed sleep
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "img.image-row-img"))
    )
    take_screenshot_in_memory(driver)
    logging.info("📸 Screenshot taken after image generation.")

    logging.info("🖼️ Extracting image blobs...")
    js_script = """
    const done = arguments[0];
    (async () => {
        const imgs = Array.from(document.querySelectorAll('img.image-row-img'));
        const promises = imgs.map(img => {
            return fetch(img.src)
                .then(res => res.blob())
                .then(blob => new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onloadend = () => resolve(reader.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(blob);
                }));
        });
        const results = await Promise.all(promises);
        done(results);
    })();
    """
    return driver.execute_async_script(js_script)

def save_base64_images(base64_list):
    saved = []
    for data_url in base64_list:
        if not data_url.startswith("data:image"):
            continue
        _, base64_data = data_url.split(",", 1)
        img_data = base64.b64decode(base64_data)
        file_id = str(uuid.uuid4())
        path = os.path.join(TEMP_IMAGE_DIR, f"{file_id}.png")
        with open(path, "wb") as f:
            f.write(img_data)
        saved.append({"url": f"/serve-image/{file_id}"})
        logging.info(f"✅ Image saved: {path}")
    return saved

@app.route("/api/gen", methods=["POST"])
def generate():
    prompt = request.args.get("prompt")
    if not prompt:
        return jsonify({"error": "Missing prompt."}), 400
    try:
        base64_images = generate_images(driver, prompt)
        saved = save_base64_images(base64_images)
        logging.info(f"✅ Generated and saved {len(saved)} images for prompt: {prompt}")
        return jsonify(saved)
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)})

@app.route("/api/screenshot")
def serve_screenshot_api():
    try:
        screenshot_png = take_screenshot_in_memory(driver)
        logging.info("✅ Screenshot served as PNG.")
        return send_file(
            BytesIO(screenshot_png),
            mimetype="image/png",
            as_attachment=False,
            download_name="screenshot.png"
        )
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route("/serve-image/<image_id>")
def serve_image(image_id):
    path = os.path.join(TEMP_IMAGE_DIR, f"{image_id}.png")
    if not os.path.exists(path):
        return jsonify({"error": "Image not found"}), 404
    logging.info(f"✅ Serving image: {path}")
    return send_file(path, mimetype="image/png")

@app.route('/restart')
def restart_browser():
    global driver
    code = request.args.get("code")
    if code != ADMIN_CODE:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    try:
        driver.quit()
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("✅ Browser session restarted.")
        return jsonify({"status": "success", "message": "Browser session restarted."})
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

def get_binary_version(binary_path):
    try:
        result = subprocess.run([binary_path, "--version"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Could not determine version: {e}"

if __name__ == '__main__':
    email = os.getenv("email")
    password = os.getenv("password")

    if not email or not password:
        print("❌ Missing email or password in .env file.")
        exit(1)

    print("🔍 Chromium version:", get_binary_version(chrome_bin))
    print("🔍 Chromedriver version:", get_binary_version(chromedriver_bin))

    try:
        login_to_bing(driver, email, password)
        logged_in = True
        print("✅ Logged in to Bing successfully.")
    except Exception as e:
        print("❌ Login failed:", e)
        exit(1)

    app.run(host='0.0.0.0', port=10000)
