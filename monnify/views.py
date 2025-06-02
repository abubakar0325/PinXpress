from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MonnifyVirtualAccount
from .utils import create_virtual_account
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseServerError
from .models import VirtualAccount
from django.views.decorators.csrf import ensure_csrf_cookie
import hmac
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from .models import MonnifyTransaction, MonnifyVirtualAccount
from django.contrib.auth import get_user_model
from django.db import transaction as db_transaction
from datetime import datetime

User = get_user_model()

# views.py
import requests
import json
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from .utils import create_virtual_account




import requests
import base64
from django.conf import settings

def get_monnify_access_token():
    url = f"{settings.MONNIFY_BASE_URL}/api/v1/auth/login"
    api_key = settings.MONNIFY_API_KEY
    secret_key = settings.MONNIFY_SECRET_KEY

    # Combine api_key and secret_key with colon and base64 encode it
    credentials = f"{api_key}:{secret_key}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/json"
    }

    # Use POST method (not GET)
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        access_token = data['responseBody']['accessToken']
        return access_token
    else:
        # Raise error with details to help debug
        raise Exception(f"Monnify API request error: {response.status_code} {response.text}")

import requests
from django.conf import settings
import base64

def get_auth_token():
    api_key = settings.MONNIFY_API_KEY
    secret_key = settings.MONNIFY_SECRET_KEY
    auth_string = f"{api_key}:{secret_key}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.monnify.com/api/v1/auth/login",
        headers=headers
    )

    print("Auth response:", response.text)

    if response.status_code == 200:
        return response.json()['responseBody']['accessToken']
    return None


@csrf_exempt
@login_required
def get_virtual_account(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Parse JSON body safely
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # Get BVN from JSON
    bvn = data.get("bvn")
    if not bvn:
        return JsonResponse({"error": "BVN is required"}, status=400)

    if len(bvn) != 11 or not bvn.isdigit():
        return JsonResponse({"error": "BVN must be exactly 11 digits"}, status=400)
    # 1. Check if virtual account already exists for this user
    try:
        existing_account = VirtualAccount.objects.get(user=request.user)
        return JsonResponse({
            "status": "exists",
            "account": {
                "account_number": existing_account.account_number,
                "bank_name": existing_account.bank_name,
                "account_reference": existing_account.account_reference,
                "status": existing_account.status
            }
        })
    except VirtualAccount.DoesNotExist:
        pass  # Continue to create new virtual account

    # 2. Get Monnify auth token
    access_token = get_auth_token()
    if not access_token:
        return JsonResponse({"error": "Failed to authenticate with Monnify"}, status=403)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    account_ref = f"wallet-{request.user.id}-02d5a5"

    payload = {
        "accountReference": account_ref,
        "accountName": f"{request.user.first_name} {request.user.last_name}",
        "currencyCode": "NGN",
        "contractCode": settings.MONNIFY_CONTRACT_CODE,
        "customerEmail": request.user.email,
        "customerName": f"{request.user.first_name} {request.user.last_name}",
        "bvn": bvn,
        "getAllAvailableBanks": True,
        "metaData": {
            "ipAddress": request.META.get("REMOTE_ADDR", "127.0.0.1"),
            "deviceType": "web"
        }
    }

    try:
        response = requests.post(
            "https://api.monnify.com/api/v1/bank-transfer/reserved-accounts",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        response_data = response.json().get("responseBody", {})

        virtual_account = VirtualAccount.objects.create(
            user=request.user,
            account_reference=response_data.get("accountReference", ""),
            account_name=response_data.get("accountName", ""),
            account_number=response_data.get("accountNumber", ""),
            bank_name=response_data.get("bankName", ""),
            bank_code=response_data.get("bankCode", ""),
            reservation_reference=response_data.get("reservationReference", ""),
            status=response_data.get("status", ""),
            bvn=bvn
        )

        return JsonResponse({
            "status": "created",
            "account": {
                "account_reference": virtual_account.account_reference,
                "account_name": virtual_account.account_name,
                "account_number": virtual_account.account_number,
                "bank_name": virtual_account.bank_name,
                "bank_code": virtual_account.bank_code,
                "reservation_reference": virtual_account.reservation_reference,
                "status": virtual_account.status,
                "bvn": virtual_account.bvn,
            }
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



@csrf_exempt
def monnify_webhook(request):
    print("Received webhook")
    print("Method:", request.method)
    print("Headers:", request.headers)
    print("Body:", request.body.decode())

    if request.method != 'POST':
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body.decode())
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    event_type = data.get("eventType")
    event_data = data.get("eventData", {})

    if event_type == "BANK_TRANSFER_SUCCESSFUL":
        account_reference = event_data.get("accountReference")
        amount_paid = event_data.get("amountPaid")

        print(f"Received payment for accountReference: {account_reference}, amount: {amount_paid}")

        try:
            virtual_account = VirtualAccount.objects.get(account_reference=account_reference)
            virtual_account.balance += float(amount_paid)
            virtual_account.save()
            print("Balance updated successfully")

            return JsonResponse({"message": "Balance updated"}, status=200)
        except VirtualAccount.DoesNotExist:
            print("Virtual account not found")
            return JsonResponse({"error": "Virtual account not found"}, status=404)
    
    print("Ignored event:", event_type)
    return JsonResponse({"message": "Event ignored"}, status=200)
    




@login_required
@ensure_csrf_cookie  # Make sure CSRF cookie is set in the response
def get_or_create_virtual_account(request):
    if request.method == 'POST':
        try:
            # Check if user already has account
            account = VirtualAccount.objects.filter(user=request.user).first()
            if account:
                data = {
                    "status": "exists",
                    "message": "Virtual account already exists.",
                    "account": {
                        "account_reference": account.account_reference,
                        "account_name": account.account_name,
                        "account_number": account.account_number,
                        "bank_name": account.bank_name,
                        "bank_code": account.bank_code,
                        "status": account.status,
                        "reservation_reference": account.reservation_reference,
                        "bvn": account.bvn,
                    }
                }
            else:
                # Create new virtual account by calling your existing function
                account_data = create_virtual_account(request)  # Return dict, not JsonResponse
                account = VirtualAccount.objects.get(account_reference=account_data['accountReference'])
                data = {
                    "status": "created",
                    "message": "Virtual account created successfully.",
                    "account": {
                        "account_reference": account.account_reference,
                        "account_name": account.account_name,
                        "account_number": account.account_number,
                        "bank_name": account.bank_name,
                        "bank_code": account.bank_code,
                        "status": account.status,
                        "reservation_reference": account.reservation_reference,
                        "bvn": account.bvn,
                    }
                }
            return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "POST request required"}, status=405)
