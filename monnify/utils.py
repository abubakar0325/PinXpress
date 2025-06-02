import requests
import base64
import hmac
from django.http import JsonResponse
import hashlib
import time
from django.conf import settings
from django.contrib.auth.decorators import login_required
import json
import uuid
from django.views.decorators.csrf import csrf_exempt

import requests
import base64

from .models import VirtualAccount
import os


def get_monnify_access_token():
    api_key = os.getenv("MONNIFY_API_KEY")
    secret_key = os.getenv("MONNIFY_SECRET_KEY")
    base_url = os.getenv("MONNIFY_BASE_URL")

    encoded_credentials = base64.b64encode(f"{api_key}:{secret_key}".encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            headers=headers
        )
        response.raise_for_status()
        return response.json()['responseBody']['accessToken']
    except requests.exceptions.RequestException as e:
        raise Exception(f"Monnify API request error: {e}")


@csrf_exempt
@login_required
def create_virtual_account(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Check if user already has a virtual account
    if hasattr(request.user, 'virtual_account'):
        return JsonResponse({"error": "Virtual account already exists"}, status=400)

    # Parse JSON body
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    bvn = body.get("bvn")
    if not bvn:
        return JsonResponse({"error": "BVN is required"}, status=400)

    # Validate BVN
    if not bvn.isdigit() or len(bvn) != 11:
        return JsonResponse({"error": "BVN must be exactly 11 digits"}, status=400)

    # Get Monnify token
    token = get_monnify_access_token()
    if not token:
        return JsonResponse({"error": "Failed to authenticate with Monnify"}, status=403)

    url = f"{settings.MONNIFY_BASE_URL}/api/v1/bank-transfer/reserved-accounts"
    account_ref = f"wallet-{request.user.id}-{uuid.uuid4().hex[:6]}"

    payload = {
        "accountReference": account_ref,
        "accountName": f"{request.user.first_name} {request.user.last_name} Wallet",
        "contractCode": settings.MONNIFY_CONTRACT_CODE,
        "currencyCode": "NGN",
        "customerEmail": request.user.email,
        "customerName": f"{request.user.first_name} {request.user.last_name}",
        "bvn": bvn,
        "getAllAvailableBanks": True,
        "incomeSplitConfig": [],
        "metaData": {
            "ipAddress": request.META.get("REMOTE_ADDR", "127.0.0.1"),
            "deviceType": "web"
        }
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json().get('responseBody', {})

        # Save account to database with OneToOne relationship enforced in model
        VirtualAccount.objects.create(
            user=request.user,
            account_reference=data.get('accountReference'),
            account_name=data.get('accountName'),
            account_number=data.get('accountNumber'),
            bank_name=data.get('bankName'),
            bank_code=data.get('bankCode'),
            status=data.get('status'),
            reservation_reference=data.get('reservationReference'),
            bvn=bvn
        )

        return JsonResponse({
            "message": "Virtual account created successfully",
            "account": data
        })

    except requests.exceptions.HTTPError:
        try:
            error_json = response.json()
        except ValueError:
            error_json = {"error": "Invalid response from Monnify"}

        return JsonResponse({
            "error": "Monnify API returned an error",
            "details": error_json
        }, status=response.status_code)

    except Exception as e:
        return JsonResponse({
            "error": "An unexpected error occurred",
            "details": str(e)
        }, status=500)
    
def get_virtual_account_details(token, account_reference):
    url = f"{settings.MONNIFY_BASE_URL}/api/v1/bank-transfer/reserved-accounts/{account_reference}"

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['responseBody']

