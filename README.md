# Nansen API Sample Dashboards

This project demonstrates how Nansen's API can help visualize onchain data revolving smart money and token flows.

## Setup

1. Create a `.streamlit/secrets.toml` file in the project root.

```toml
apiKey = "YOUR_NANSEN_API_KEY"
NANSEN_BASE_URL= "https://api.nansen.ai/api/v1"

[auth]
redirect_uri = "YOUR_REDIRECT_URI"
cookie_secret = "YOUR_COOKIE_SECRET"
client_id = "YOUR_CLIENT_ID"
client_secret = "YOUR_CLIENT_SECRET"
server_metadata_url = "YOUR_SERVER_METADATA_URL"
```

**Note:**

- Retrieve the above secrets from **Google's Console Authentication**.


2. Install dependencies (using a virtual environment):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Note:**

- Run `pip install --upgrade pip` if needed.
- Use `pip3` instead of `pip` if needed.
- If you see dependency conflicts (e.g., scipy vs numpy), activate the `.venv` and reinstall requirements.

3. Run the Streamlit app:

```bash
streamlit run Landing_Page.py --server.port 8501
```

4. View app at [http://localhost:8501](http://localhost:8501)