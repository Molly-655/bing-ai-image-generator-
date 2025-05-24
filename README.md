# bing-image-creator
AUTOMATION OF GENERATION OF IMAGE USING BING

# 🖼️ Bing Image Creator API

Effortlessly generate images using Bing's powerful image generation engine, automated with Selenium and a Flask-based RESTful API.  
Easily integrate Bing's creativity into your own apps, bots, or workflows!

---

<p align="center">
  <img src="https://user-images.githubusercontent.com/3369400/273451341-7ad1f4b3-efc1-4c6d-b0c6-6b8e0a2f8eb8.png" width="500" alt="Bing Image Creator Demo"/>
</p>

---

## 🚀 Features

- **API-driven Bing Image Generation**  
  Send prompts, receive images—fully automated with headless browser tech.
- **Random API Key Generation**  
  Secure your endpoints with a rotating pool of API keys.
- **Session Management**  
  Refresh or restart browser sessions on demand.
- **Web UI**  
  Generate and copy API keys instantly from the homepage.
- **Image Serving Endpoint**  
  Directly serve generated images via a REST endpoint.
- **Robust Error Handling**  
  User-friendly error pages and JSON responses.
- **Easy Integration**  
  Use with Python, cURL, Postman, or any tool that supports HTTP requests.

---

## 🛠️ Requirements

- Python 3.8+
- Google Chrome or Chromium
- ChromeDriver (matching your Chrome version)
- [Microsoft account](https://signup.live.com/) (must already exist!)
- Bing Image Creator access enabled for that Microsoft account

---

## ⚡️ Quickstart

1. **Clone the repository**
    ```bash
    git clone https://github.com/Sman12345678/bing-image-creator.git
    cd bing-image-creator
    ```

2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure your environment**

    Create a `.env` file in the root directory:

    ```env
    email=your-microsoft-account-email@outlook.com
    password=your_microsoft_password
    ```

    > **Important:**  
    > - The email **must have been used to create a Microsoft account before**.
    > - For security, use an account dedicated for automation (not your main personal account).

4. **Download [ChromeDriver](https://chromedriver.chromium.org/downloads)**  
   and place it in your PATH. Though it's already handled properly so it's OPTIONAL

5. **Run the server**
    ```bash
    python app.py
    ```
    The API will be running at `http://localhost:10000`.

---

## 🎮 Usage Examples

### **Get an API key**

```bash
curl http://localhost:10000/api/getkey
```

### **Generate images**

```bash
curl -X POST http://localhost:10000/api/gen \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY", "prompt": "a futuristic city at sunset"}'
```

**Response Example:**
```json
[
  {"url": "/serve-image/bb3e7f81-0a31-4c3d-b77b-7e9f9a1b2a8c"},
  {"url": "/serve-image/7ec6d084-c6a9-4d08-8c36-4f9e841c1ed2"}
]
```

### **Serve a generated image**

You can access your generated images directly through the `/serve-image/<image_id>` endpoint after generation.

```bash
curl http://localhost:10000/serve-image/bb3e7f81-0a31-4c3d-b77b-7e9f9a1b2a8c --output myimage.png
```
Or simply open in your browser:
```
http://localhost:10000/serve-image/bb3e7f81-0a31-4c3d-b77b-7e9f9a1b2a8c
```
> Replace `bb3e7f81-0a31-4c3d-b77b-7e9f9a1b2a8c` with your actual image ID from the API response.

---

### **Refresh or Restart browser session**

- Refresh (no relogin):  
  `POST http://localhost:10000/refresh-browser`
- Restart (with relogin):  
  `POST http://localhost:10000/restart`

---

## 🖥️ Web User Interface

Visit [http://localhost:10000/](http://localhost:10000/) in your browser for a simple UI to:
- Generate and copy API keys
- See example API usage

---

## 💡 Tips

- **API keys are required** for image generation—grab one from the homepage or `/api/getkey`.
- If you encounter login issues, ensure your email is a valid Microsoft account and not protected with 2FA or unusual authentication.
- For stability, use a **dedicated Microsoft account** just for this bot.

---

## 🧩 API Reference

### `POST /api/gen`

| Parameter   | Type   | Description                      |
|-------------|--------|----------------------------------|
| api_key     | str    | Your API key (from `/api/getkey`)|
| prompt      | str    | The image prompt                 |

**Response:**  
- On success: JSON array of image URLs (use with `/serve-image/<image_id>`).
- On error: JSON error message or error page.

### `GET /api/getkey`

Returns a random API key.

### `POST /refresh-browser`  
Refresh the browser session (no relogin).

### `POST /restart`  
Restart the browser and relogin.

### `GET /serve-image/<image_id>`

- Serves the PNG image corresponding to the given image ID.
- Example:  
  ```
  http://localhost:10000/serve-image/7ec6d084-c6a9-4d08-8c36-4f9e841c1ed2
  ```

---

## 🛡️ Security

- **Never share your API key** publicly.
- Use environment variables or a `.env` file to keep credentials secure.
- If deploying publicly, protect endpoints and implement rate limiting.

---

## 🗨️ Support & Contact

- **Questions? Bugs? Feature requests?**  
  Open an [issue](https://github.com/Sman12345678/bing-image-creator/issues) on GitHub.

- **Need direct help? Contact me:**  
  - **Facebook/WhatsApp:** `+2348088941798`

---

## ⭐️ Show Your Support

If you found this project useful or cool, please ⭐️ star the repo and share with others!

---

<p align="center">
  <img src="https://grupoioe.es/wp-content/uploads/2025/03/bing_image_creator.webp" width="300" alt="Bing Image Creator Icon"/>
</p>

---

> _This project is not affiliated with Microsoft or Bing.  
> Use for educational or research purposes only._
