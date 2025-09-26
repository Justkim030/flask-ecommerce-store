import os
import requests
from dotenv import load_dotenv

load_dotenv()

def initiate_mpesa_charge(phone_number, amount, email="customer@example.com", reference=None):
    """
    Initiates an M-Pesa charge via Paystack.
    """
    paystack_secret_key = os.environ.get('PAYSTACK_SECRET_KEY')
    if not paystack_secret_key:
        return {"error": "Paystack secret key not configured."}

    # Format phone number to international format if needed
    if phone_number.startswith('0'):
        phone_number = '254' + phone_number[1:]
    elif not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    # Amount in kobo (Paystack uses kobo, 1 KES = 100 kobo)
    amount_kobo = int(amount * 100)

    url = "https://api.paystack.co/charge"
    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",
        "Content-Type": "application/json"
    }
    data = {
        "amount": amount_kobo,
        "email": email,
        "currency": "KES",
        "mobile_money": {
            "phone": phone_number,
            "provider": "Mpesa"
        }
    }
    if reference:
        data["reference"] = reference

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code} - {response.text}"}
    except Exception as e:
        return {"error": str(e)}
