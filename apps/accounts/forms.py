from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import User, InviteToken


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"


class InviteForm(forms.Form):
    """owner/admin 이 팀원 초대할 때."""
    email = forms.EmailField(
        label="이메일",
        widget=forms.EmailInput(attrs={"class": INPUT_CLS, "placeholder": "teammate@company.com"}),
    )
    role = forms.ChoiceField(
        label="역할",
        choices=[
            ("admin", "관리자"),
            ("intake", "접수"),
            ("agent", "상담사"),
        ],
        widget=forms.Select(attrs={"class": INPUT_CLS}),
    )
    manager = forms.ModelChoiceField(
        label="직속 상사 (선택)",
        queryset=User.objects.none(),  # view 에서 주입
        required=False,
        empty_label="(직접 배속)",
        widget=forms.Select(attrs={"class": INPUT_CLS}),
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            # 동일 회사 내에서 상사 후보
            self.fields["manager"].queryset = User.objects.filter(company=company, is_active=True).order_by("name")


class AcceptInviteForm(forms.Form):
    """초대 토큰 받은 사람이 계정 생성할 때."""
    name = forms.CharField(
        label="이름", max_length=100,
        widget=forms.TextInput(attrs={"class": INPUT_CLS}),
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
        pw = self.cleaned_data["password"]
        validate_password(pw)
        return pw
