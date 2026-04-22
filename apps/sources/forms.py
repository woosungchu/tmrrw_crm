from django import forms
from .models import Source


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"


class SourceForm(forms.ModelForm):
    class Meta:
        model = Source
        fields = ["title", "is_active", "tmrw_form_id"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "광고 랜딩 · 자사 폼 · 제휴사 등"}),
            "tmrw_form_id": forms.TextInput(attrs={"class": INPUT_CLS, "placeholder": "(선택) tmrw_web form_id"}),
        }


class ApiKeyLabelForm(forms.Form):
    label = forms.CharField(
        label="키 라벨",
        max_length=100, required=False,
        widget=forms.TextInput(attrs={
            "class": INPUT_CLS,
            "placeholder": "예: 프로덕션, 테스트, 파트너A",
        }),
    )
