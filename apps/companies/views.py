from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect

from .forms import SignupForm
from .services import create_company_with_owner


def landing(request):
    return render(request, 'public/landing.html')


def signup(request):
    if request.user.is_authenticated:
        return redirect('/app/')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            company, owner = create_company_with_owner(
                company_name=form.cleaned_data['company_name'],
                owner_name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                login_id=form.cleaned_data['login_id'],
                password=form.cleaned_data['password'],
            )
            login(request, owner)
            messages.success(request, f"{company.name} 가입 완료! 14일 무료 체험 시작.")
            return redirect('/app/')
    else:
        form = SignupForm()

    return render(request, 'public/signup.html', {'form': form})
