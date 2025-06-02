from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings

from .models import PastQuestion, Purchase, ExamCategory
from .utils import generate_token, verify_token


@login_required
def initiate_payment(request, question_id):
    question = get_object_or_404(PastQuestion, id=question_id)

    if request.method == 'POST':
        return redirect('pastquestions:question_detail', pk=question.id)

    return render(request, 'pastquestions/initiate_payment.html', {'question': question})



@login_required
def buy_past_question(request, question_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    user = request.user
    question = get_object_or_404(PastQuestion, id=question_id)
    price = question.price

    if user.balance < price:
        return JsonResponse({'error': 'Insufficient balance'}, status=402)

    try:
        # Deduct balance
        user.balance -= price
        user.save()

        # Create purchase record
        Purchase.objects.create(
            user=user,
            question=question,
            payment_reference=f"wallet-{user.username}-{question.id}"
        )

        # Generate secure download token
        token = generate_token(user, question.id)
        download_url = request.build_absolute_uri(
            reverse('pastquestions:secure_download', args=[token])
        )

        # Send email with download link
        email = EmailMessage(
            subject=f"Your Purchased Question: {question.title}",
            body=f"""Dear {user.username},

Thank you for purchasing '{question.title}'.

You can securely download your file using the link below. The link will expire in 1 hour:
{download_url}

Best regards,
Your Website Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.send()

        return JsonResponse({'success': True, 'message': f"You have successfully bought '{question.title}'! A download link has been sent to your email."})

    except Exception as e:
        print(f"Purchase error: {e}")
        return JsonResponse({'error': 'An error occurred during purchase.'}, status=500)

def question_list(request):
    categories = ExamCategory.objects.all()
    questions = PastQuestion.objects.all()
    return render(request, 'pastquestions/list.html', {'questions': questions, 'categories': categories})


def question_detail(request, pk):
    question = get_object_or_404(PastQuestion, pk=pk)
    return render(request, 'pastquestions/details.html', {'question': question})


@login_required
def download_question_file(request, question_id):
    user = request.user
    try:
        # Get the most recent purchase
        purchase = Purchase.objects.filter(user=user, question_id=question_id).latest('timestamp')
        file_path = purchase.question.file.path
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=purchase.question.file.name)

    except Purchase.DoesNotExist:
        raise Http404("You have not purchased this question.")
    except Exception as e:
        print(f"Download error: {e}")
        raise Http404("An error occurred while downloading the file.")


@login_required
def my_purchases(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-purchased_at')
    return render(request, 'pastquestions/purchase_history.html', {'purchases': purchases})


@login_required
def secure_download(request, token):
    user_id, question_id = verify_token(token)

    if not user_id or user_id != request.user.id:
        raise Http404("Invalid or expired download link.")

    try:
        purchase = Purchase.objects.filter(user_id=user_id, question_id=question_id).latest('timestamp')
        file_path = purchase.question.file.path
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=purchase.question.title + ".pdf")
    except Purchase.DoesNotExist:
        raise Http404("No valid purchase found for this file.")
    except Exception as e:
        print(f"Secure download error: {e}")
        raise Http404("An error occurred during secure download.")
