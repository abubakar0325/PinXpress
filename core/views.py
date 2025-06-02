from django.shortcuts import render

from django.shortcuts import render

def home_view(request):
    return render(request, 'core/home.html')


def past_questions_waec(request):
    return render(request, 'core/past_questions_waec.html')
