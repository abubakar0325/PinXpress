from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives



from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from datetime import datetime

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
import qrcode

def generate_pin_pdf(user, pins):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # === Add Watermark ===
    p.saveState()
    p.setFont("Helvetica-Bold", 40)
    p.setFillGray(0.85, 0.5)  # Light gray, semi-transparent
    p.translate(width / 2, height / 2)
    p.rotate(45)
    p.drawCentredString(0, 0, "PinXpress")
    p.restoreState()

    # === Add QR Code ===
    qr_data = f"Username: {user.username}\nEmail: {user.email}"
    qr = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr.save(qr_buffer)
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)
    p.drawImage(qr_image, width - 150, height - 150, width=100, height=100)

    # === Add Main Content ===
    p.setFont("Helvetica", 14)
    p.drawString(50, height - 50, f"Purchased Exam Pins for {user.username}")

    y = height - 100
    for pin in pins:
        # Assuming 'serial_number' is the field name of your pin's serial number
        p.drawString(50, y, f"{pin.name} PIN: {pin.pin}  S/N: {pin.serial}")
        y -= 25

        if y < 100:  # Go to next page if too long
            p.showPage()
            y = height - 100

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer



def send_activation_email(user, request):
    current_site = get_current_site(request)
    subject = "Activate Your Account"
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = f"http://{current_site.domain}/activate/{uid}/{token}/"

    html_content = render_to_string('accounts/activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })

    email = EmailMultiAlternatives(
        subject=subject,
        body="Please use an HTML-compatible email viewer to read this message.",
        from_email='help@resultcheck.buzz',
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)