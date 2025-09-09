import os
import requests
from requests.auth import HTTPBasicAuth
import base64
from datetime import datetime

# Load M-PESA credentials from environment variables
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_BUSINESS_SHORTCODE = os.environ.get('MPESA_BUSINESS_SHORTCODE')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL') # e.g., https://your-app.on-render.com/mpesa_callback

# Use sandbox URLs for development/testing
API_AUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"

def get_mpesa_access_token():
    """
    Makes a request to the Safaricom API to get an access token.
    Returns a tuple (access_token, error_message).
    """
    if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
        error_msg = "M-PESA Consumer Key or Secret not configured in environment variables."
        print(error_msg)
        return None, error_msg
        
    try:
        res = requests.get(API_AUTH_URL, auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET))
        res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return res.json().get('access_token'), None
    except requests.exceptions.RequestException as e:
        # Safaricom often returns error details in the response body even on failure
        error_details = str(e)
        if e.response is not None:
            try:
                # Try to parse JSON error response from Safaricom
                error_details = e.response.json()
            except ValueError: # Not a JSON response
                error_details = e.response.text
        
        error_msg = f"API request failed. Details: {error_details}"
        print(f"Error getting M-PESA access token: {error_msg}")
        return None, error_msg

def initiate_stk_push(phone_number, amount, account_reference="TechKenya", transaction_desc="Payment for goods"):
    """
    Initiates an M-PESA STK Push request.
    """
    # --- 1. Validation Step: Ensure all required credentials are set ---
    required_vars = {
        "MPESA_BUSINESS_SHORTCODE": MPESA_BUSINESS_SHORTCODE,
        "MPESA_PASSKEY": MPESA_PASSKEY,
        "MPESA_CALLBACK_URL": MPESA_CALLBACK_URL
    }
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        error_msg = f"Missing M-PESA environment variables: {', '.join(missing_vars)}"
        print(error_msg)
        return {"error": "Server configuration error.", "details": error_msg}

    access_token, error = get_mpesa_access_token()
    if error:
        # Propagate the detailed error from the token function
        return {"error": "Could not get access token.", "details": error}

    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Generate the M-PESA password
    password_data = f"{MPESA_BUSINESS_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_data.encode()).decode('utf-8')

    # Format phone number to Safaricom's required format (e.g., 2547...)
    if phone_number.startswith('+'):
        phone_number = phone_number[1:]
    elif phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]

    payload = {
        "BusinessShortCode": MPESA_BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(int(amount)), # Amount must be an integer string
        "PartyA": phone_number,
        "PartyB": MPESA_BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(STK_PUSH_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error initiating STK push: {e}")
        # Provide more detailed error from the API response if possible
        error_details = e.response.json() if e.response else str(e)
        return {"error": "STK Push failed.", "details": error_details}