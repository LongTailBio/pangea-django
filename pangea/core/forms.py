from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import PangeaUser


class PangeaUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = PangeaUser
        fields = ('email',)


class PangeaUserChangeForm(UserChangeForm):

    class Meta:
        model = PangeaUser
        fields = ('email',)
