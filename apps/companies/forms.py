from django import forms
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from .models import AssignmentConfig


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"


class SignupForm(forms.Form):
    company_name = forms.CharField(
        label="회사명", max_length=200,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "(주)내일마케팅컴퍼니"}),
    )
    name = forms.CharField(
        label="담당자 이름", max_length=100,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "홍길동"}),
    )
    email = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(attrs={"class": INPUT_CLS, "placeholder": "you@company.com"}),
    )
    phone = forms.CharField(
        label="전화번호", max_length=20, required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "010-1234-5678"}),
    )
    login_id = forms.CharField(
        label="아이디", max_length=50,
        widget=forms.TextInput(attrs={"class": INPUT_CLS}),
    )
    password = forms.CharField(
        label="비밀번호", min_length=8,
        widget=forms.PasswordInput(attrs={"class": INPUT_CLS}),
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


WEEKDAY_CHOICES = [
    (0, "월"), (1, "화"), (2, "수"), (3, "목"),
    (4, "금"), (5, "토"), (6, "일"),
]


class AssignmentConfigForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        label="운영 요일",
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = AssignmentConfig
        fields = ["auto_on", "weekdays", "time_start", "time_end", "tie_breaker"]
        widgets = {
            "time_start": forms.TimeInput(attrs={"type": "time", "class": INPUT_CLS}),
            "time_end": forms.TimeInput(attrs={"type": "time", "class": INPUT_CLS}),
            "tie_breaker": forms.Select(attrs={"class": INPUT_CLS}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # DB 에 JSON 으로 저장된 weekdays 를 MultipleChoiceField 가 이해하도록 변환
        if self.instance and self.instance.pk:
            self.initial["weekdays"] = [str(d) for d in (self.instance.weekdays or [])]

    def clean_weekdays(self):
        raw = self.cleaned_data.get("weekdays") or []
        return sorted(int(d) for d in raw)
