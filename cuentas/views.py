from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# ---------- Autenticación ----------

def registro(request):
    if request.method == 'POST':
        username = request.POST.get('reg_username', '').strip()
        email = request.POST.get('reg_email', '').strip()
        password = request.POST.get('reg_password', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Ese nombre de usuario ya existe.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Ese correo ya está registrado.')
        else:
            try:
                validate_password(password)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
            else:
                user = User.objects.create_user(
                    username=username, email=email, password=password
                )
                login(request, user)
                return redirect('home')

    return render(request, 'cuentas/register.html')


def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'cuentas/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Pantallas ----------

@login_required
def home(request):
    return render(request, 'cuentas/home.html', {'activo': 'inicio'})


@login_required
def diagnostico(request):
    return render(request, 'cuentas/diagnostico.html', {'activo': 'diagnostico'})


@login_required
def plan(request):
    return render(request, 'cuentas/plan.html', {'activo': 'plan'})


@login_required
def accion(request):
    return render(request, 'cuentas/accion.html', {'activo': 'plan'})


@login_required
def seguimiento(request):
    return render(request, 'cuentas/seguimiento.html', {'activo': 'progreso'})