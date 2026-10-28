from django.db import transaction
from .models import (Accion, Area, Brecha, Diagnostico, PlantillaAccion,
                     Pregunta, Prioridad, Respuesta)

VALOR_MAX = 3          # valor más alto de una respuesta
UMBRAL_ALTA = 40       # puntaje < 40  -> severidad Alta
UMBRAL_MEDIA = 70      # puntaje < 70  -> severidad Media; el resto, Baja

TEXTOS_BRECHA = {
    'gestion': {
        3: 'Uso muy limitado de herramientas digitales en la gestión',
        2: 'Uso parcial de herramientas digitales en la gestión',
        1: 'Gestión interna con buen nivel de digitalización',
    },
    'comercial': {
        3: 'Casi sin presencia en canales digitales',
        2: 'Presencia parcial en canales digitales',
        1: 'Buena presencia en canales digitales',
    },
    'finanzas': {
        3: 'Falta de registro y análisis de datos',
        2: 'Registro y análisis de datos parcial',
        1: 'Finanzas con buen registro y análisis de datos',
    },
}


def severidad_por_puntaje(puntaje):
    if puntaje < UMBRAL_ALTA:
        return Prioridad.ALTA
    if puntaje < UMBRAL_MEDIA:
        return Prioridad.MEDIA
    return Prioridad.BAJA


@transaction.atomic
def crear_diagnostico(pyme, respuestas):
    """Crea el diagnóstico a partir de {id_pregunta: valor}.

    Calcula el puntaje de cada área y crea una brecha por área.
    Lanza ValueError si falta alguna respuesta.
    """
    preguntas = list(Pregunta.objects.filter(activa=True))
    if not preguntas or any(str(p.id) not in respuestas for p in preguntas):
        raise ValueError('Faltan respuestas')

    diag = Diagnostico.objects.create(pyme=pyme)
    totales = {area: [0, 0] for area in Area.values}  # [suma, máximo posible]

    for p in preguntas:
        valor = respuestas[str(p.id)]
        Respuesta.objects.create(diagnostico=diag, pregunta=p, valor=valor)
        totales[p.area][0] += valor
        totales[p.area][1] += VALOR_MAX

    puntajes = []
    for area, (suma, maximo) in totales.items():
        if maximo == 0:
            continue
        puntaje = round(suma * 100 / maximo)
        severidad = int(severidad_por_puntaje(puntaje))
        Brecha.objects.create(
            diagnostico=diag, area=area, puntaje=puntaje,
            severidad=severidad, detalle=TEXTOS_BRECHA[area][severidad],
        )
        puntajes.append(puntaje)

    promedio = sum(puntajes) / len(puntajes)
    diag.nivel = min(5, int(promedio // 20) + 1)   # 0-19 -> 1 ... 80+ -> 5
    diag.save(update_fields=['nivel'])
    return diag


@transaction.atomic
def generar_plan(diagnostico):
    """Asigna las acciones prefabricadas según el puntaje de cada área.

    Las áreas con peor puntaje (mayor severidad) van primero.
    Si el plan ya existe no hace nada, así un doble clic no duplica acciones.
    """
    if diagnostico.acciones.exists():
        return diagnostico.acciones.all()

    orden = 1
    for brecha in diagnostico.brechas.all():  # de mayor a menor severidad
        plantillas = PlantillaAccion.objects.filter(
            area=brecha.area,
            puntaje_min__lte=brecha.puntaje,
            puntaje_max__gte=brecha.puntaje,
        )
        for plantilla in plantillas:
            Accion.objects.create(
                diagnostico=diagnostico,
                titulo=plantilla.titulo,
                area=brecha.area,
                descripcion=plantilla.descripcion,
                pasos=plantilla.pasos,
                prioridad=brecha.severidad,
                orden=orden,
            )
            orden += 1
    return diagnostico.acciones.all()


def calcular_progreso(acciones):
    total = len(acciones)
    completadas = sum(1 for a in acciones if a.estado == 'completada')
    return {
        'total': total,
        'completadas': completadas,
        'en_progreso': sum(1 for a in acciones if a.estado == 'en_progreso'),
        'pendientes': sum(1 for a in acciones if a.estado == 'pendiente'),
        'porcentaje': round(completadas * 100 / total) if total else 0,
    }