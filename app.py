import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import base64
import re
import requests

st.title("Auto Deliver Software After PayPal Payment")

# Authenticate with Google using Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
)

# Gmail API setup
service = build("gmail", "v1", credentials=creds)

def get_latest_payment_email():
    query = 'from:service@intl.paypal.com subject:"You’ve received"'
    result = service.users().messages().list(userId="me", q=query, maxResults=1).execute()
    messages = result.get("messages", [])
    if not messages:
        return None, None
    msg = service.users().messages().get(userId="me", id=messages[0]["id"]).execute()
    headers = msg["payload"]["headers"]
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "")
    sender = next((h["value"] for h in headers if h["name"] == "From"), "")
    parts = msg["payload"].get("parts", [])
    body = ""
    if parts:
        for part in parts:
            if part["mimeType"] == "text/plain":
                data = part["body"]["data"]
                body = base64.urlsafe_b64decode(data).decode("utf-8")
                break
    return subject, sender

def generate_download_link(buyer_email):
    res = requests.post("https://your-fly-app.fly.dev/generate", json={"email": buyer_email})
    if res.status_code == 200:
        return res.json().get("link")
    return None

if st.button("Check PayPal Email"):
    subject, sender = get_latest_payment_email()
    if subject:
        st.success(f"Found Email: {subject} from {sender}")
        email_match = re.search(r'from (.+?) \(', subject)
        buyer_email = email_match.group(1).strip() if email_match else "unknown"
        download_link = generate_download_link(buyer_email)
        if download_link:
            st.info(f"Send this download link to buyer: {download_link}")
        else:
            st.error("Failed to generate download link.")
    else:
        st.warning("No recent PayPal payment email found.")
