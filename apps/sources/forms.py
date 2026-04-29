from django import forms
from .models import Source


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"


class SourceForm(forms.ModelForm):
    # scheme 없이 입력해도 https:// 자동 보정. 진짜 이상한 값일 때만 에러.
    noti_webhook_url = forms.URLField(
        required=False,
        assume_scheme="https",
        max_length=500,
        error_messages={
            "invalid": "올바른 URL 형식이 아닙니다. http:// 또는 https:// 로 시작해야 합니다.",
        },
        # type=text + inputmode=url — 브라우저 native URL 검증 우회.
        # 서버에서 assume_scheme 으로 보정하기 위함.
        widget=forms.TextInput(attrs={
            "class": INPUT_CLS,
            "placeholder": "(선택) https://기존시스템/webhook  (또는 www.example.com)",
            "inputmode": "url",
            "autocomplete": "url",
        }),
    )

    class Meta:
        model = Source
        fields = ["title", "is_active", "tmrw_form_id", "noti_webhook_url"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "광고 랜딩 · 자사 폼 · 제휴사 등"}),
            "tmrw_form_id": forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "(선택) tmrw_web form_id"}),
        }

    def clean_noti_webhook_url(self):
        url = self.cleaned_data.get("noti_webhook_url", "")
        if url and not (url.startswith("http://") or url.startswith("https://")):
            raise forms.ValidationError(
                "올바른 URL 형식이 아닙니다. http:// 또는 https:// 로 시작해야 합니다."
            )
        return url


class ApiKeyLabelForm(forms.Form):
    label = forms.CharField(
        label="키 라벨",
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            "class": INPUT_CLS,
            "placeholder": "예: 프로덕션, 테스트, 파트너A",
        }),
    )
