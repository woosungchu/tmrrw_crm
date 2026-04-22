from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def app_home(request):
    """로그인 후 랜딩. W5 전까지 placeholder — 본인 회사·역할 확인용."""
    return render(request, 'app/home.html')
