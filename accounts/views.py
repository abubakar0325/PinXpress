from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model, logout, login, authenticate
from monnify.utils import get_virtual_account_details
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from monnify.models import VirtualAccount
from .forms import ResendActivationForm
import logging
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa
from .utils import generate_pin_pdf
from monnify.utils import get_monnify_access_token
from django.core.mail import EmailMessage
from .forms import WalletTopUpForm
from django.shortcuts import get_object_or_404
from .models import TopUpTransaction
from .forms import UserRegisterForm, BuyExamPinForm
from django.views.decorators.csrf import csrf_exempt
from .models import ExamPin
from django.http import HttpResponseNotAllowed, HttpResponse
from .forms import UserEditForm 
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import FileResponse, Http404
from django.contrib.sites.shortcuts import get_current_site
import io
from .models import TopUpTransaction, PurchaseTransaction
import uuid
from io import BytesIO
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import send_mail

@login_required
def all_transaction_history(request):
    search_query = request.GET.get('search', '')

    topups = TopUpTransaction.objects.filter(user=request.user).order_by('-timestamp')
    purchases = PurchaseTransaction.objects.filter(user=request.user).order_by('-timestamp')

    if search_query:
        topups = topups.filter(transaction_id__icontains=search_query)
        purchases = purchases.filter(transaction_id__icontains=search_query)

    return render(request, 'accounts/history.html', {
        'topups': topups,
        'purchases': purchases,
        'search_query': search_query,
    })


logger = logging.getLogger(__name__)
# REGISTER VIEW

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User inactive until email confirmed
            user.save()

            # Send activation email
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('accounts/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(
                mail_subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, 'Please confirm your email address to complete registration.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
# LOGIN VIEW
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('dashboard')  # Redirect to user dashboard
            else:
                messages.error(request, "Account inactive. Please check your email to activate.")
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')

import requests
from django.conf import settings

@login_required
def dashboard_view(request):
    
    exam_pins = [
        {
            'name': 'WAEC Scratch Card',
            'price': 3500,
            'image_url': '/static/accounts/waec_scratch.png',
            'available': True,
        },
        {
            'name': 'NECO TOKEN',
            'price': 1150,
            'image_url': '/static/accounts/neco_token.png',
            'available': True,
        },
        {
            'name': 'NABTEB Scratch Card',
            'price': 820,
            'image_url': '/static/accounts/nabteb_scratch.png',
            'available': False,
        },
        {
            'name': 'WAEC Verification Pin',
            'price': 3350,
            'image_url': '/static/accounts/waec_verification.png',
            'available': True,
        },
        {
            'name': 'NBAIS Scratch Card',
            'price': 1280,
            'image_url': '/static/accounts/nbais_scratch.png',
            'available': True,
        },
        {
            'name': 'WAEC GCE Registration Card',
            'price': 28600,
            'image_url': '/static/accounts/waec_gce.png',
            'available': True,
        },
        {
            'name': 'NECO e-VERIFICATION PIN',
            'price': 5850,
            'image_url': '/static/accounts/neco_everify.png',
            'available': True,
        },
        {
            'name': 'EXAMINIFY BIOMETRIC TOKEN',
            'price': 190,
            'image_url': '/static/accounts/examinify_biometric.jpg',
            'available': True,
        },
    ]


    virtual_accounts = VirtualAccount.objects.filter(user=request.user)

    context = {
        'exam_pins': exam_pins,
        'virtual_accounts': virtual_accounts,  # Pass queryset to template
    }

    return render(request, 'accounts/dashboard.html', context)


User = get_user_model()



def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.email_confirmed = True 
        user.save()
        login(request, user)
        messages.success(request, "Account activated successfully! You are now logged in.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect('register')

# LOGOUT VIEW

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('login')
    elif request.method == 'GET':
        # Show confirmation page
        return render(request, 'accounts/logout_confirm.html')
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])
    

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep the user logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


''
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {
        'user': request.user
    })


@login_required
def buy_exam_pin(request):
    available_pins = ExamPin.objects.filter(is_used=False)
    pin_price_map = {
        'WAEC Scratch Card': 3500,
        'NECO TOKEN': 1150,
        'NABTEB Scratch Card': 820,
        'WAEC Verification Pin': 3350,
        'NBAIS Scratch Card': 1280,
        'WAEC GCE Registration Card': 28600,
        'NECO e-VERIFICATION PIN': 5850,
        'EXAMINIFY BIOMETRIC TOKEN': 190,
    }

    purchased_pins = []

    if request.method == 'POST':
        pin_name = request.POST.get('pin_name')
        quantity = int(request.POST.get('quantity', 1))
        price = pin_price_map.get(pin_name, 0)
        total_price = price * quantity

        available_of_type = ExamPin.objects.filter(name=pin_name, is_used=False)

        if available_of_type.count() < quantity:
            messages.error(request, "Not enough pins available for your request.")
            return redirect('buy_exam_pin')

        if request.user.balance < total_price:
            messages.error(request, "Insufficient balance.")
            return redirect('buy_exam_pin')

        # Select and mark pins as used
        purchased_pins = list(available_of_type[:quantity])
        for pin in purchased_pins:
            pin.is_used = True
            pin.save()

        # Deduct user balance
        request.user.balance -= total_price
        request.user.save()

        # Log transaction
        PurchaseTransaction.objects.create(
            user=request.user,
            product=pin_name,
            quantity=quantity,
            description=f"Purchase of {pin_name} pin(s), quantity: {quantity}",
            product_type="exam_pin",
            product_id=purchased_pins[0].id if purchased_pins else None,
            amount=total_price,
            status="success",
            timestamp=timezone.now()
        )

        # Generate PDF
        pdf_buffer = generate_pin_pdf(request.user, purchased_pins)

        # Send Email
        email = EmailMessage(
            subject="Your Purchased Exam Pins - PinXpress",
            body=f"Dear {request.user.username},\n\nPlease find attached your purchased exam pins.",
            to=[request.user.email]
        )
        email.attach(f"{request.user.username}_exam_pins.pdf", pdf_buffer.getvalue(), 'application/pdf')
        email.send()

        # Store session flags for GET success display
        request.session['purchased_pin_ids'] = [pin.id for pin in purchased_pins]
        request.session['purchase_success'] = True

        messages.success(request, f"{quantity} pin(s) for {pin_name} purchased successfully. PDF sent to your email.")
        return redirect('buy_exam_pin')

    # ---- GET Request Handler ----
    purchased_pin_ids = request.session.get('purchased_pin_ids')
    if purchased_pin_ids:
        purchased_pins = ExamPin.objects.filter(id__in=purchased_pin_ids)
        #del request.session['purchased_pin_ids']

    # ✅ Retrieve success flag
    purchase_success = request.session.pop('purchase_success', False)

    # Prepare available pin names for disabling options
    available_pin_names = {pin.name: True for pin in available_pins}

    return render(request, 'accounts/buy_exam_pin.html', {
        'available_pins': available_pins,
        'pin_price_map': pin_price_map,
        'available_pin_names': available_pin_names,
        'purchased_pins': purchased_pins,
        'purchase_success': purchase_success,
    })

@login_required
def wallet_top_up(request):
    virtual_accounts = VirtualAccount.objects.filter(user=request.user)
    return render(request, 'accounts/wallet_top_up.html', {'virtual_accounts': virtual_accounts})



@login_required
def download_pin_pdf(request):
    pin_ids = request.session.get('purchased_pin_ids')
    if not pin_ids:
        messages.error(request, "No pins available for download. Please make a new purchase.")
        return redirect('buy_exam_pin')

    pins = ExamPin.objects.filter(id__in=pin_ids)
    pdf_buffer = generate_pin_pdf(request.user, pins)

    # ✅ Optionally clean the session now
    del request.session['purchased_pin_ids']

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{request.user.username}_exam_pins.pdf"'
    return response


@login_required
def generate_pdf_report(request):
    topups = TopUpTransaction.objects.filter(user=request.user)
    purchases = PurchaseTransaction.objects.filter(user=request.user)

    template_path = 'transactions/pdf_template.html'
    context = {'topups': topups, 'purchases': purchases}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="transaction_report.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa.CreatePDF(html, dest=response)
    return response


def resend_activation_view(request):
    if request.method == 'POST':
        form = ResendActivationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                if user.is_active:
                    messages.info(request, "Your account is already active. Please login.")
                else:
                    # Send activation email
                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    activation_link = request.build_absolute_uri(f"/accounts/activate/{uid}/{token}/")

                    subject = 'Activate your account'
                    message = render_to_string('accounts/activation_email.html', {
                        'user': user,
                        'activation_link': activation_link,
                    })

                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
                    messages.success(request, "Activation link has been resent to your email.")
            except User.DoesNotExist:
                messages.error(request, "No user found with this email.")
            return redirect('resend_activation')
    else:
        form = ResendActivationForm()
    return render(request, 'accounts/resend_activation.html', {'form': form})