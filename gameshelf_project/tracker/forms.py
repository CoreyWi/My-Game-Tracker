from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Game, Platform


class GameForm(forms.ModelForm):
    """Add or edit a game. The owner is set in the view, not by the user."""

    new_platform = forms.CharField(
        max_length=50,
        required=False,
        label="Or add a new platform",
        help_text="Leave blank if you picked one above.",
    )

    field_order = ["title", "platform", "new_platform", "status", "times_beaten", "notes"]

    class Meta:
        model = Game
        fields = ["title", "platform", "status", "times_beaten", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.fields["platform"].required = False
        self.fields["platform"].queryset = Platform.objects.all()

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Title can't be blank.")
        return title

    def clean(self):
        cleaned = super().clean()
        platform = cleaned.get("platform")
        new_name = (cleaned.get("new_platform") or "").strip()

        if not platform and not new_name:
            raise forms.ValidationError("Pick a platform or type a new one.")
        if new_name:
            platform = Platform.objects.filter(name__iexact=new_name).first()
            if platform is None:
                platform = Platform.objects.create(name=new_name)
            cleaned["platform"] = platform

        status = cleaned.get("status")
        beaten = cleaned.get("times_beaten") or 0
        if status in (Game.COMPLETED, Game.HUNDRED) and beaten == 0:
            cleaned["times_beaten"] = 1

        title = cleaned.get("title")
        if title and platform and self.owner:
            dupes = Game.objects.filter(
                owner=self.owner, title__iexact=title, platform=platform
            )
            if self.instance.pk:
                dupes = dupes.exclude(pk=self.instance.pk)
            if dupes.exists():
                raise forms.ValidationError(
                    f"'{title}' on {platform} is already on your shelf."
                )
        return cleaned

    def save(self, commit=True):
        game = super().save(commit=False)
        game.platform = self.cleaned_data["platform"]
        game.times_beaten = self.cleaned_data["times_beaten"]
        if self.owner is not None:
            game.owner = self.owner
        if commit:
            game.save()
        return game


class BeatForm(forms.Form):
    """Optional note when logging that you beat a game."""

    note = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Optional note (e.g. hard mode)"}),
    )


class SignUpForm(UserCreationForm):
    """Member sign-up using Django's built-in user model."""

    class Meta(UserCreationForm.Meta):
        fields = ("username",)