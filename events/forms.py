from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Event, Registration
import re

User = get_user_model()

DEPARTMENT_CHOICES = [
    ("", "-- Select Department --"),
    ("Computer Engineering", "Computer Engineering"),
    ("Information Technology", "Information Technology"),
    ("Electronics & Telecommunication", "Electronics & Telecommunication"),
    ("Mechanical Engineering", "Mechanical Engineering"),
    ("Civil Engineering", "Civil Engineering"),
    ("Electrical Engineering", "Electrical Engineering"),
    ("Artificial Intelligence & Data Science", "Artificial Intelligence & Data Science"),
    ("MBA / Management", "MBA / Management"),
    ("Other", "Other"),
]

INPUT_CLASS = (
    "w-full h-10 px-3 text-sm bg-white border border-[#CBD5E0] rounded-[4px] "
    "text-[#1A202C] placeholder-[#718096] focus:outline-none focus:border-[#1F3A5F] "
    "focus:ring-1 focus:ring-[#1F3A5F] transition-colors duration-150"
)

TEXTAREA_CLASS = (
    "w-full min-h-[90px] p-3 text-sm bg-white border border-[#CBD5E0] rounded-[4px] "
    "text-[#1A202C] placeholder-[#718096] focus:outline-none focus:border-[#1F3A5F] "
    "focus:ring-1 focus:ring-[#1F3A5F] transition-colors duration-150 resize-y"
)

SELECT_CLASS = (
    "w-full h-10 px-3 text-sm bg-white border border-[#CBD5E0] rounded-[4px] "
    "text-[#1A202C] focus:outline-none focus:border-[#1F3A5F] focus:ring-1 "
    "focus:ring-[#1F3A5F] transition-colors duration-150 cursor-pointer"
)


def apply_widget_styles(form_instance):
    for field_name, field in form_instance.fields.items():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.update({
                "class": "w-4 h-4 text-[#1F3A5F] border-[#CBD5E0] rounded-[4px] focus:ring-[#1F3A5F]"
            })
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs.update({"class": TEXTAREA_CLASS, "rows": 3})
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.update({"class": SELECT_CLASS})
        else:
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{INPUT_CLASS} {existing}".strip()


class ModernBaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)


class LoginForm(ModernBaseForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Username", "autofocus": True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "id": "login-password"})
    )


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "category", "event_date", "venue", "description", "fee", "capacity"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Event title"}),
            "category": forms.Select(),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "venue": forms.TextInput(attrs={"placeholder": "Venue"}),
            "description": forms.Textarea(attrs={"placeholder": "Event description and details", "rows": 3}),
            "fee": forms.NumberInput(attrs={"placeholder": "0.00", "min": "0", "step": "0.50"}),
            "capacity": forms.NumberInput(attrs={"placeholder": "Capacity", "min": "1"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)

    def clean_event_date(self):
        event_date = self.cleaned_data.get("event_date")
        if not event_date:
            return event_date

        today = timezone.localdate()
        is_new = not self.instance or not self.instance.pk
        date_changed = (not is_new) and (self.instance.event_date != event_date)

        if (is_new or date_changed) and event_date < today:
            raise ValidationError("Event date cannot be in the past.")

        return event_date

    def clean_capacity(self):
        capacity = self.cleaned_data.get("capacity")
        if capacity is None or capacity <= 0:
            raise ValidationError("Capacity must be a positive integer greater than zero.")
        if self.instance and self.instance.pk:
            active_count = self.instance.active_registrations_count
            if capacity < active_count:
                raise ValidationError(
                    f"Capacity cannot be reduced below current active registrations ({active_count})."
                )
        return capacity

    def clean_fee(self):
        fee = self.cleaned_data.get("fee")
        if fee is None or fee < 0:
            raise ValidationError("Event fee cannot be negative.")
        return fee


class StudentCreationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Full name"})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    roll_no = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Roll number"})
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.Select()
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "Email address"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password (minimum 4 characters)"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(f"Username '{username}' is already taken.")
        return username

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get("roll_no", "").strip().upper()
        if not roll_no:
            raise ValidationError("Roll number cannot be empty.")
        if User.objects.filter(roll_no__iexact=roll_no).exists():
            raise ValidationError(f"Roll number '{roll_no}' is already registered.")
        return roll_no

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError(f"Email '{email}' is already registered.")
        return email or None

    def clean_password(self):
        password = self.cleaned_data.get("password", "")
        if len(password) < 4:
            raise ValidationError("Password must be at least 4 characters long.")
        return password


class StudentUpdateForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Full name"})
    )
    roll_no = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={"placeholder": "Roll number"})
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.Select()
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "Email address"})
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"placeholder": "New password (leave blank to keep current)"})
    )

    def __init__(self, *args, user_instance=None, **kwargs):
        self.user_instance = user_instance
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get("roll_no", "").strip().upper()
        if not roll_no:
            raise ValidationError("Roll number cannot be empty.")
        qs = User.objects.filter(roll_no__iexact=roll_no)
        if self.user_instance:
            qs = qs.exclude(pk=self.user_instance.pk)
        if qs.exists():
            raise ValidationError(f"Roll number '{roll_no}' is already registered.")
        return roll_no

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if email:
            qs = User.objects.filter(email__iexact=email)
            if self.user_instance:
                qs = qs.exclude(pk=self.user_instance.pk)
            if qs.exists():
                raise ValidationError(f"Email '{email}' is already in use.")
        return email or None

    def clean_new_password(self):
        pw = self.cleaned_data.get("new_password", "")
        if pw and len(pw) < 4:
            raise ValidationError("Password must be at least 4 characters long.")
        return pw


class StudentRegisterForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        label="Full name",
        widget=forms.TextInput(attrs={"placeholder": "Full name"})
    )
    username = forms.CharField(
        max_length=150,
        label="Username",
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    roll_no = forms.CharField(
        max_length=50,
        label="Roll number",
        widget=forms.TextInput(attrs={"placeholder": "Roll number"})
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        label="Department",
        widget=forms.Select()
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"placeholder": "Email address"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Password (minimum 4 characters)"})
    )
    confirm_password = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_widget_styles(self)

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken.")
        return username

    def clean_roll_no(self):
        roll_no = self.cleaned_data.get("roll_no", "").strip().upper()
        if not roll_no:
            raise ValidationError("Roll number is required.")
        if User.objects.filter(roll_no__iexact=roll_no).exists():
            raise ValidationError("This roll number is already registered.")
        return roll_no

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        cpw = cleaned_data.get("confirm_password")
        if pw and cpw and pw != cpw:
            self.add_error("confirm_password", "Passwords do not match.")
        if pw and len(pw) < 4:
            self.add_error("password", "Password must be at least 4 characters long.")
        return cleaned_data
