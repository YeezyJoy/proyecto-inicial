from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST

from .models import Accion, Area, Pregunta, OPCIONES_RESPUESTA
from .servicios import generar_plan, calcular_progreso, crear_diagnostico

AREAS_POR_PASO = {1: Area.GESTION, 2: Area.COMERCIAL, 3: Area.FINANZAS}


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
                user = User.objects.create_user(username=username, email=email, password=password)
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


# ---------- Ayudas internas ----------

def _pyme_y_diagnostico(request):
    pyme = request.user.pymes.first()
    diag = pyme.diagnosticos.first() if pyme else None
    return pyme, diag


def _sin_diagnostico(request):
    messages.info(request, 'Primero responde la encuesta de diagnóstico.')
    return redirect('encuesta', paso=1)


# ---------- Pantallas ----------

@login_required
def home(request):
    pyme, diag = _pyme_y_diagnostico(request)
    return render(request, 'cuentas/home.html', {
        'activo': 'inicio', 'pyme': pyme, 'diag': diag,
        'pymes': request.user.pymes.all(),
    })


@login_required
def encuesta(request, paso):
    if paso not in AREAS_POR_PASO:
        raise Http404

    pyme = request.user.pymes.first()
    if pyme is None:
        messages.info(request, 'Primero necesitas una Pyme registrada.')
        return redirect('home')

    area = AREAS_POR_PASO[paso]
    preguntas = list(Pregunta.objects.filter(area=area, activa=True))
    respuestas = request.session.get('encuesta', {})

    if request.method == 'POST':
        faltan = False
        for p in preguntas:
            valor = request.POST.get(f'p_{p.id}')
            if valor in ('0', '1', '2', '3'):
                respuestas[str(p.id)] = int(valor)
            else:
                faltan = True
        request.session['encuesta'] = respuestas

        if faltan:
            messages.error(request, 'Responde todas las preguntas para continuar.')
        elif paso < 3:
            return redirect('encuesta', paso=paso + 1)
        else:
            try:
                crear_diagnostico(pyme, respuestas)
            except ValueError:
                messages.error(request, 'Faltan respuestas de pasos anteriores.')
                return redirect('encuesta', paso=1)
            request.session.pop('encuesta', None)
            messages.success(request, 'Diagnóstico calculado. Revisa tus resultados.')
            return redirect('diagnostico')

    for p in preguntas:
        p.actual = respuestas.get(str(p.id))   # para marcar lo ya respondido

    return render(request, 'cuentas/encuesta.html', {
        'activo': 'diagnostico',
        'paso': paso,
        'avance': round((paso - 1) * 100 / 3),
        'area_nombre': Area(area).label,
        'preguntas': preguntas,
        'opciones': OPCIONES_RESPUESTA,
    })


@login_required
def diagnostico(request):
    pyme, diag = _pyme_y_diagnostico(request)
    if diag is None:
        return _sin_diagnostico(request)
    return render(request, 'cuentas/diagnostico.html', {
        'activo': 'diagnostico', 'pyme': pyme, 'diag': diag,
        'brechas': diag.brechas.all(), 'niveles': range(1, 6),
    })


@login_required
@require_POST
def crear_plan(request):
    pyme, diag = _pyme_y_diagnostico(request)
    if diag is None:
        return _sin_diagnostico(request)
    acciones = generar_plan(diag)
    if acciones.exists():
        messages.success(request, 'Plan generado según las prioridades del diagnóstico.')
    else:
        messages.warning(request, 'No hay acciones en el catálogo para las brechas detectadas.')
    return redirect('plan')


@login_required
def plan(request):
    pyme, diag = _pyme_y_diagnostico(request)
    if diag is None:
        return _sin_diagnostico(request)
    acciones = list(diag.acciones.all())
    return render(request, 'cuentas/plan.html', {
        'activo': 'plan', 'pyme': pyme,
        'acciones': acciones, 'progreso': calcular_progreso(acciones),
    })


@login_required
def seguimiento(request):
    pyme, diag = _pyme_y_diagnostico(request)
    if diag is None:
        return _sin_diagnostico(request)
    acciones = list(diag.acciones.all())
    return render(request, 'cuentas/seguimiento.html', {
        'activo': 'progreso', 'pyme': pyme,
        'acciones': acciones, 'progreso': calcular_progreso(acciones),
    })


@login_required
def accion(request, accion_id):
    # Solo acciones del propio usuario
    accion = get_object_or_404(Accion, id=accion_id, diagnostico__pyme__usuario=request.user)

    if request.method == 'POST':
        nuevo = request.POST.get('estado')
        if nuevo in Accion.Estado.values:
            accion.estado = nuevo
            accion.save(update_fields=['estado', 'actualizado'])
            messages.success(request, 'Estado actualizado.')
        return redirect('plan')

    return render(request, 'cuentas/accion.html', {
        'activo': 'plan', 'accion': accion, 'estados': Accion.Estado.choices,
    })