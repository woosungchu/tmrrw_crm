from django import forms

from apps.accounts.models import User
from apps.sources.models import Source
from .models import Lead, Blacklist


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"
SELECT_CLS = INPUT_CLS  # 동일 스타일


class LeadManualForm(forms.Form):
    """수동 리드 등록 (owner/admin/intake)."""
    source = forms.ModelChoiceField(
        label="유입 채널",
        queryset=Source.objects.none(),
        widget=forms.Select(attrs={"class": SELECT_CLS}),
    )
    name = forms.CharField(
        label="이름", max_length=100, required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLS}),
    )
    phone = forms.CharField(
        label="전화번호", max_length=20, required=False,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "01012345678"}),
    )
    agent = forms.ModelChoiceField(
        label="담당 상담사 (선택)", required=False,
        queryset=User.objects.none(), empty_label="(미배정)",
        widget=forms.Select(attrs={"class": SELECT_CLS}),
    )
    memo = forms.CharField(
        label="메모 (선택)", required=False,
        widget=forms.Textarea(attrs={"class": INPUT_CLS, "rows": 3}),
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["source"].queryset = Source.objects.filter(company=company, is_active=True)
            self.fields["agent"].queryset = User.objects.filter(
                company=company, role__in=["agent", "admin", "owner"], is_active=True,
            ).order_by("name")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("name") and not cleaned.get("phone"):
            raise forms.ValidationError("이름과 전화번호 중 하나는 입력해주세요.")
        return cleaned


class BlacklistManualForm(forms.Form):
    """블랙리스트 수동 추가."""
    phone = forms.CharField(
        label="전화번호",
        max_length=20,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "01012345678"}),
    )
    reason = forms.CharField(
        label="사유",
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "예: 장난 전화, 스팸"}),
    )

    def clean_phone(self):
        v = self.cleaned_data["phone"]
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 7:
            raise forms.ValidationError("유효한 전화번호를 입력해주세요.")
        return v
