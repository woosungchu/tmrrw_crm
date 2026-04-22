from django import forms
from django.contrib.auth.password_validation import validate_password
from apps.accounts.models import User


class SignupForm(forms.Form):
    company_name = forms.CharField(
        label="회사명", max_length=200,
        widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500",
                                       "placeholder": "(주)내일마케팅컴퍼니"}),
    )
    name = forms.CharField(
        label="담당자 이름", max_length=100,
        widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500",
                                       "placeholder": "홍길동"}),
    )
    email = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500",
                                        "placeholder": "you@company.com"}),
    )
    phone = forms.CharField(
        label="전화번호", max_length=20, required=False,
        widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500",
                                       "placeholder": "010-1234-5678"}),
    )
    login_id = forms.CharField(
        label="아이디", max_length=50,
        widget=forms.TextInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"}),
    )
    password = forms.CharField(
        label="비밀번호", min_length=8,
        widget=forms.PasswordInput(attrs={"class": "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"}),
    )

    def clean_login_id(self):
        login_id = self.cleaned_data["login_id"]
        if User.objects.filter(login_id=login_id).exists():
            raise forms.ValidationError("이미 사용중인 아이디입니다.")
        return login_id

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password
