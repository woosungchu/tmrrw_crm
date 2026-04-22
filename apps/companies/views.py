from django.shortcuts import render


def landing(request):
    return render(request, 'public/landing.html')


def signup(request):
    # W2 에서 본격 구현. 지금은 placeholder.
    return render(request, 'public/landing.html')
