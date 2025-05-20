from flask import Flask, jsonify, request, send_file
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess
import os
import time
import logging
import base64
import uuid
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

TEMP_IMAGE_DIR = "temp_images"
SCREENSHOT_DIR = "screenshots"
os.makedirs(TEMP_IMAGE_DIR, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ADMIN_CODE = "ICU14CU"

chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/chromium")
chromedriver_bin = os.getenv("CHROMEDRIVER_BIN", "/usr/bin/chromedriver")

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

def take_screenshot(driver, name):
    filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(filepath)
    logging.info(f"📸 Screenshot saved: {filepath}")

def login_to_bing(driver, email, password):
    driver.get("https://www.bing.com/images/create")
    logging.info("🔁 Navigating to Join & Create...")
    take_screenshot(driver, "home")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "create_btn_c"))).click()
    time.sleep(3)

    logging.info("📧 Entering email...")
    driver.find_element(By.ID, "usernameEntry").send_keys(email)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
    time.sleep(3)
    take_screenshot(driver, "email")

    logging.info("🔑 Using password login...")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Use your password']"))).click()
    time.sleep(2)
    take_screenshot(driver, "clip")

    logging.info("🔒 Entering password...")
    driver.find_element(By.ID, "passwordEntry").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[data-testid='primaryButton']").click()
    time.sleep(3)
    take_screenshot(driver, "password")

    logging.info("✅ Staying signed in...")
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='primaryButton']"))).click()
    time.sleep(5)
    take_screenshot(driver, "signed")

def generate_images(driver, prompt):
    logging.info("🖊️ Typing prompt...")
    textarea = driver.find_element(By.ID, "sb_form_q")
    textarea.clear()
    textarea.send_keys(prompt)
    driver.find_element(By.ID, "create_btn_c").click()
    time.sleep(15)
    take_screenshot(driver, "create")

    logging.info("🖼️ Extracting image blobs...")
    js_script = """
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
    return Promise.all(promises);
    """
    return driver.execute_async_script(f"const done = arguments[0]; ({js_script}).then(done)")

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
    return saved

@app.route("/api/gen", methods=["POST"])
def generate():
    email = os.getenv("email")
    password = os.getenv("password")
    prompt = request.args.get("prompt")

    if not all([email, password, prompt]):
        return jsonify({"error": "Missing email, password, or prompt."}), 400

    try:
        login_to_bing(driver, email, password)
        base64_images = generate_images(driver, prompt)
        saved = save_base64_images(base64_images)
        return jsonify(saved)
    except Exception as e:
        logging.error(traceback.format_exc())
        return jsonify({"error": str(e)})

@app.route("/screenshots")
def list_screenshots():
    files = [f for f in os.listdir(SCREENSHOT_DIR) if f.endswith(".png")]
    links = [f'<li><a href="/screenshots/{f}" target="_blank">{f}</a></li>' for f in files]
    html = f"<h2>📸 Available Screenshots</h2><ul>{''.join(links)}</ul>"
    return html

@app.route("/screenshots/<filename>")
def serve_screenshot(filename):
    path = os.path.join(SCREENSHOT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Screenshot not found"}), 404
    return send_file(path, mimetype="image/png")

@app.route("/serve-image/<image_id>")
def serve_image(image_id):
    path = os.path.join(TEMP_IMAGE_DIR, f"{image_id}.png")
    if not os.path.exists(path):
        return jsonify({"error": "Image not found"}), 404
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
        return jsonify({"status": "success", "message": "Browser session restarted."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def get_binary_version(binary_path):
    try:
        result = subprocess.run([binary_path, "--version"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Could not determine version: {e}"

if __name__ == '__main__':
    print("Chromium version:", get_binary_version(chrome_bin))
    print("Chromedriver version:", get_binary_version(chromedriver_bin))
    app.run(host='0.0.0.0', port=10000)
