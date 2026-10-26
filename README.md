# Telegram Account Name Service

A lightweight web service and API to display and update your Telegram account name via Telethon MTProto, with Swagger API documentation and an automatic keepalive pinger for Render.

---

## Interactive API Documentation

- **Swagger UI:** **[http://localhost:8000/docs](http://localhost:8000/docs)** (Interactive testing of all endpoints directly in browser)
- **ReDoc:** **[http://localhost:8000/redoc](http://localhost:8000/redoc)**
- **OpenAPI Schema:** `GET /openapi.json`

---

## Configuration

Credentials (`API_ID`, `API_HASH`, and `SESSION_STRING`) are hardcoded directly in [`config.py`](file:///c:/Users/Jisan/Desktop/playground/config.py). No `.env` file or environment variables are required.

---

## Deploying to Render

Since credentials are built directly into the codebase, deploying to Render requires no environment variable configuration:

1. Push your repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com/), click **New +** > **Web Service**.
3. Select your repository.
4. Set:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**.

---

## Keepalive Pinger (`/ping`)

To prevent the service from sleeping on Render's free tier (which spins down after 15 minutes of inactivity):

- **Health Check Endpoint:** `GET /ping`
- **Self-Pinger:** The application runs an automatic background pinger:
  - If on Render, it automatically detects your live URL via Render's `RENDER_EXTERNAL_URL` environment variable and pings itself every 10 minutes.
  - You can also optionally specify a custom URL via the `PING_URL` environment variable.

---

## API Endpoints

### 1. View Account Name
- **URL:** `GET /name`
- **Response:**
  ```json
  {
    "name": "Galif",
    "first_name": "Galif",
    "last_name": ""
  }
  ```

### 2. Update Account Name
- **URL:** `POST /name`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "name": "New Name"
  }
  ```
- **Response:**
  ```json
  {
    "success": true,
    "message": "Account name updated successfully",
    "name": "New Name",
    "first_name": "New",
    "last_name": "Name"
  }
  ```
