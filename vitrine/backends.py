from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOuUsuarioBackend(ModelBackend):
    """Entra com o e-mail (sem diferenciar maiúsculas) ou, nas contas antigas, com o usuário."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if not username or password is None:
            return None
        username = username.strip()
        user = (User.objects.filter(username=username).first()
                or User.objects.filter(email__iexact=username).order_by('id').first())
        if user is None:
            User().set_password(password)  # mesmo tempo de resposta quando a conta não existe
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
