# Nansen API Sample Dashboards

This project demonstrates how Nansen's API can help visualize onchain data revolving smart money and token flows.

## Setup

1. Refer to `.streamlit/secrets.toml.example` and create a `secrets.toml` file in the same directory.

```toml
nansen_api_key = "your_api_key_here"
openai_api_key= "your_openai_api_key_here"

nansen_api_url = "https://api.nansen.ai/api/v1" # v1 example
nansen_mcp_url = "https://mcp.nansen.ai/ra/mcp/"

[hl]
secret_key = "" # get from app.hyperliquid-testnet.xyz/API for testnet or app.hyperliquid.xyz/API for mainnet
account_address = "" # not the api wallet address, but your wallet address

[auth]
redirect_uri = "http://localhost:8501/oauth2callback" # or your deployed URL
cookie_secret = "your_cookie_secret_here"
client_id = "your_client_id_here"
client_secret = "your_client_secret_here"
server_metadata_url = "your_server_metadata_url_here" # if using Google OAuth: https://accounts.google.com/.well-known/openid-configuration
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


# ML Notebooks

Wallet Clustering: https://drive.google.com/drive/folders/1H7py-5kRgreLaPlbPIscBHkkFNNPePh3?usp=sharing

Token Returns: https://drive.google.com/drive/folders/1TYefy7f-M7D3Tgimcw11GUH168fCv7rZ?usp=sharing
