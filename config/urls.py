from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.views.static import serve
from django.urls import re_path, include, path

from vitrine.forms import EsqueciSenhaForm, NovaSenhaForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('entrar/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    path('sair/', auth_views.LogoutView.as_view(), name='logout'),
    path('senha/esqueci/', auth_views.PasswordResetView.as_view(
        template_name='registration/senha_esqueci.html',
        email_template_name='registration/senha_email.txt',
        subject_template_name='registration/senha_assunto.txt',
        form_class=EsqueciSenhaForm), name='password_reset'),
    path('senha/enviado/', auth_views.PasswordResetDoneView.as_view(template_name='registration/senha_enviado.html'), name='password_reset_done'),
    path('senha/nova/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/senha_nova.html', form_class=NovaSenhaForm), name='password_reset_confirm'),
    path('senha/pronto/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/senha_pronto.html'), name='password_reset_complete'),
    # fotos enviadas pelos comerciantes (protótipo: o próprio Django entrega os arquivos)
    re_path(r'^midia/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('', include('vitrine.urls')),
]
