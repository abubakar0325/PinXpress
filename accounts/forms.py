from django import forms
from .models import CustomUser, ExamPin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    agree = forms.BooleanField(required=True, label="I agree to the Terms and Conditions")

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'address', 'phone_number', 'nin_or_bvn', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if CustomUser.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_nin_or_bvn(self):
        nin = self.cleaned_data['nin_or_bvn']
        if CustomUser.objects.filter(nin_or_bvn=nin).exists():
            raise forms.ValidationError("This NIN or BVN is already registered.")
        return nin

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']





class BuyExamPinForm(forms.Form):
    pin_type = forms.ModelChoiceField(
        queryset=ExamPin.objects.filter(is_used=False).distinct('name'),
        empty_label="Select Exam Pin Type",
        label="Exam Pin Type"
    )


class WalletTopUpForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=100, label="Top-Up Amount (₦)")


class ResendActivationForm(forms.Form):
    email = forms.EmailField(label="Your email", widget=forms.EmailInput(attrs={'class': 'form-control'}))