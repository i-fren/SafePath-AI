from django import forms
from .models import TrustedContact, SafetyReport, Journey


class TrustedContactForm(forms.ModelForm):
    class Meta:
        model = TrustedContact
        fields = ['name', 'phone', 'email', 'relationship', 'is_primary']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 300 1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mother, Friend, Brother'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SafetyReportForm(forms.ModelForm):
    class Meta:
        model = SafetyReport
        fields = ['report_type', 'severity', 'title', 'description', 'latitude', 'longitude']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide details...'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
        }


class StartJourneyForm(forms.Form):
    source_lat = forms.FloatField(widget=forms.HiddenInput())
    source_lng = forms.FloatField(widget=forms.HiddenInput())
    dest_lat = forms.FloatField(widget=forms.HiddenInput())
    dest_lng = forms.FloatField(widget=forms.HiddenInput())
    source_name = forms.CharField(max_length=300, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Source location'}
    ))
    dest_name = forms.CharField(max_length=300, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Destination'}
    ))
    checkin_interval = forms.ChoiceField(
        choices=[('0', 'Disabled'), ('15', '15 minutes'), ('30', '30 minutes'), ('60', '60 minutes')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='0'
    )
    contacts = forms.ModelMultipleChoiceField(
        queryset=TrustedContact.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contacts'].queryset = TrustedContact.objects.filter(user=user)
