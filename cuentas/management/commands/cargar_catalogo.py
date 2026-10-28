from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from cuentas.models import Pyme, Pregunta, PlantillaAccion

PREGUNTAS = {
    'gestion': [
        'Usamos una herramienta digital para controlar el inventario o los insumos.',
        'Las tareas y responsabilidades del equipo están organizadas en una herramienta digital.',
        'Los documentos importantes del negocio están guardados de forma digital.',
        'El equipo sabe usar las herramientas digitales básicas (correo, planillas, mensajería).',
        'Coordinamos con proveedores y con el equipo mediante medios digitales.',
    ],
    'comercial': [
        'El negocio tiene perfiles activos en redes sociales.',
        'Publicamos productos o promociones en línea con regularidad.',
        'Los clientes pueden contactarnos o pedir por canales digitales (WhatsApp, web, etc.).',
        'El negocio aparece en Google Maps o en directorios en línea.',
        'Medimos qué publicaciones o canales nos traen más clientes.',
    ],
    'finanzas': [
        'Registramos ventas y gastos en una planilla o programa, no solo en papel.',
        'Aceptamos pagos con tarjeta o transferencia.',
        'Revisamos las ventas cada mes para tomar decisiones.',
        'Emitimos boletas o facturas electrónicas.',
        'Conocemos los costos y márgenes de nuestros productos.',
    ],
}

# (área, título, descripción, pasos, puntaje_min, puntaje_max)
CATALOGO = [
    ('gestion', 'Implementar sistema de inventario',
     'Implementar una herramienta digital para registrar y controlar el inventario de productos, lo que permitirá evitar quiebres de stock y mejorar la planificación de compras.',
     'Evaluar las herramientas recomendadas\nRegistrar el inventario actual\nCapacitar al equipo en el uso de la herramienta', 0, 69),
    ('gestion', 'Capacitar al equipo en herramientas básicas',
     'Entrenar al equipo en el uso de herramientas digitales del día a día.',
     'Definir los contenidos\nAgendar la capacitación\nEvaluar los resultados', 0, 59),
    ('gestion', 'Organizar las tareas del equipo con una herramienta digital',
     'Usar un tablero o aplicación para repartir y seguir las tareas.',
     'Elegir la herramienta\nCargar las tareas actuales\nRevisar el avance cada semana', 40, 100),
    ('comercial', 'Crear redes sociales del negocio',
     'Abrir perfiles del negocio para llegar a más clientes y mostrar los productos.',
     'Elegir las plataformas\nCrear los perfiles\nPublicar los primeros productos', 0, 59),
    ('comercial', 'Registrar el negocio en Google Maps',
     'Aparecer en búsquedas locales con horarios, dirección y fotos.',
     'Crear la ficha del negocio\nVerificar la dirección\nSubir fotos y horarios', 0, 79),
    ('comercial', 'Medir los resultados de las publicaciones',
     'Revisar qué contenidos generan más consultas y ventas.',
     'Definir indicadores simples\nRevisar las estadísticas cada mes\nRepetir lo que mejor funciona', 50, 100),
    ('finanzas', 'Utilizar medios de pago digitales',
     'Incorporar pagos con tarjeta o transferencia para facilitar la venta.',
     'Comparar proveedores\nContratar el servicio\nProbar un cobro', 0, 69),
    ('finanzas', 'Registrar ventas y gastos en una planilla',
     'Dejar de depender del papel para saber cuánto entra y cuánto sale.',
     'Crear la planilla\nRegistrar las ventas de cada día\nRegistrar los gastos de la semana', 0, 59),
    ('finanzas', 'Analizar datos de ventas mensuales',
     'Revisar las ventas cada mes para tomar mejores decisiones.',
     'Armar un resumen mensual\nDetectar tendencias\nAjustar compras y precios', 30, 100),
]


class Command(BaseCommand):
    help = 'Carga preguntas y catálogo de acciones. Opcional: crea una Pyme de ejemplo para un usuario.'

    def add_arguments(self, parser):
        parser.add_argument('username', nargs='?', help='Usuario al que crearle una Pyme si no tiene')

    def handle(self, *args, **options):
        if not Pregunta.objects.exists():
            for area, textos in PREGUNTAS.items():
                for i, texto in enumerate(textos):
                    Pregunta.objects.create(area=area, texto=texto, orden=i)
            self.stdout.write('Preguntas creadas.')

        # El catálogo se recrea; las acciones ya generadas no se ven afectadas (son copias).
        PlantillaAccion.objects.all().delete()
        for i, (area, titulo, desc, pasos, pmin, pmax) in enumerate(CATALOGO):
            PlantillaAccion.objects.create(
                area=area, titulo=titulo, descripcion=desc, pasos=pasos,
                puntaje_min=pmin, puntaje_max=pmax, orden=i)
        self.stdout.write('Catálogo de acciones recreado.')

        username = options.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError('Ese usuario no existe.')
            if not user.pymes.exists():
                Pyme.objects.create(usuario=user, nombre='Panadería El Valle',
                                    rubro='Alimentación', tamano='Pequeña', region='Valparaíso')
                self.stdout.write('Pyme de ejemplo creada.')

        self.stdout.write(self.style.SUCCESS('Listo.'))
    