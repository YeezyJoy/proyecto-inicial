from django.conf import settings
from django.db import models


class Area(models.TextChoices):
    GESTION = 'gestion', 'Gestión interna'
    COMERCIAL = 'comercial', 'Comercialización'
    FINANZAS = 'finanzas', 'Finanzas'


class Prioridad(models.IntegerChoices):
    BAJA = 1, 'Baja'
    MEDIA = 2, 'Media'
    ALTA = 3, 'Alta'


OPCIONES_RESPUESTA = [
    (0, 'No'),
    (1, 'Parcialmente'),
    (2, 'En gran parte'),
    (3, 'Totalmente'),
]

COLOR_PRIORIDAD = {3: 'danger', 2: 'warning', 1: 'success'}
COLOR_ESTADO = {'pendiente': 'secondary', 'en_progreso': 'warning', 'completada': 'success'}


class Pyme(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pymes')
    nombre = models.CharField(max_length=120)
    rubro = models.CharField(max_length=80)
    tamano = models.CharField('tamaño', max_length=40)
    region = models.CharField(max_length=80)

    def __str__(self):
        return self.nombre


class Diagnostico(models.Model):
    pyme = models.ForeignKey(Pyme, on_delete=models.CASCADE, related_name='diagnosticos')
    fecha = models.DateField(auto_now_add=True)
    nivel = models.PositiveSmallIntegerField(default=1, help_text='Madurez digital de 1 a 5')

    class Meta:
        ordering = ['-fecha', '-id']

    @property
    def nivel_texto(self):
        return {1: 'Inicial', 2: 'Básico', 3: 'Intermedio', 4: 'Avanzado', 5: 'Líder'}.get(self.nivel, '')

    def __str__(self):
        return f'Diagnóstico de {self.pyme} ({self.fecha})'


class Brecha(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='brechas')
    area = models.CharField(max_length=20, choices=Area.choices)
    detalle = models.CharField(max_length=200)
    severidad = models.PositiveSmallIntegerField(choices=Prioridad.choices, default=Prioridad.MEDIA)
    puntaje = models.PositiveSmallIntegerField(default=0, help_text='Puntaje del área, de 0 a 100')

    class Meta:
        ordering = ['-severidad', 'id']

    @property
    def color(self):
        return COLOR_PRIORIDAD[self.severidad]

    def __str__(self):
        return f'{self.get_area_display()} ({self.get_severidad_display()})'


class Pregunta(models.Model):
    area = models.CharField(max_length=20, choices=Area.choices)
    texto = models.CharField(max_length=250)
    orden = models.PositiveSmallIntegerField(default=0)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['area', 'orden']

    def __str__(self):
        return self.texto


class Respuesta(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    valor = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('diagnostico', 'pregunta')


class PlantillaAccion(models.Model):
    """Acción prefabricada del catálogo. Se asigna si el puntaje del área cae en su rango."""
    area = models.CharField(max_length=20, choices=Area.choices)
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    pasos = models.TextField(help_text='Un paso por línea')
    puntaje_min = models.PositiveSmallIntegerField(default=0)
    puntaje_max = models.PositiveSmallIntegerField(default=100)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['area', 'orden']

    def __str__(self):
        return self.titulo


class Accion(models.Model):
    """Acción concreta del plan de una Pyme (copia de una plantilla)."""

    class Estado(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        EN_PROGRESO = 'en_progreso', 'En progreso'
        COMPLETADA = 'completada', 'Completada'

    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name='acciones')
    titulo = models.CharField(max_length=150)
    area = models.CharField(max_length=20, choices=Area.choices)
    descripcion = models.TextField()
    pasos = models.TextField()
    prioridad = models.PositiveSmallIntegerField(choices=Prioridad.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    orden = models.PositiveSmallIntegerField()
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden']

    @property
    def lista_pasos(self):
        return [p.strip() for p in self.pasos.splitlines() if p.strip()]

    @property
    def color_prioridad(self):
        return COLOR_PRIORIDAD[self.prioridad]

    @property
    def color_estado(self):
        return COLOR_ESTADO[self.estado]

    def __str__(self):
        return self.titulo