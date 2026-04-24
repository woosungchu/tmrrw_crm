from django import forms
from django.utils import timezone

from .models import Template, Callback


INPUT_CLS = "w-full px-3 py-2 border border-slate-300 rounded focus:outline-none focus:border-indigo-500"


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ["title", "body", "channel", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": INPUT_CLS}),
            "body": forms.Textarea(attrs={"class": INPUT_CLS, "rows": 6}),
            "channel": forms.Select(attrs={"class": INPUT_CLS}),
        }


class SendSmsForm(forms.Form):
    """lead_detail 의 SMS 발송 — 템플릿 선택 or 프리폼."""
    template = forms.ModelChoiceField(
        label="템플릿",
        queryset=Template.objects.none(),
        required=False,
        empty_label="(프리폼)",
        widget=forms.Select(attrs={"class": INPUT_CLS}),
    )
    body = forms.CharField(
        label="본문",
        required=False,
        widget=forms.Textarea(attrs={"class": INPUT_CLS, "rows": 4}),
    )

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["template"].queryset = Template.objects.filter(
                company=company, is_active=True,
            )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("template") and not (cleaned.get("body") or "").strip():
            raise forms.ValidationError("템플릿 선택 또는 본문 입력 중 하나가 필요합니다.")
        return cleaned


class CallbackForm(forms.ModelForm):
    scheduled_at = forms.DateTimeField(
        label="예약 시각",
        widget=forms.DateTimeInput(
            attrs={"class": INPUT_CLS, "type": "datetime-local"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"],
    )
    note = forms.CharField(
        label="메모",
        required=False,
        widget=forms.Textarea(attrs={"class": INPUT_CLS, "rows": 3}),
    )

    class Meta:
        model = Callback
        fields = ["scheduled_at", "note"]

    def clean_scheduled_at(self):
        v = self.cleaned_data["scheduled_at"]
        if v < timezone.now():
            raise forms.ValidationError("과거 시각은 예약할 수 없습니다.")
        return v
