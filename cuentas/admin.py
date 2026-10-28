from django.contrib import admin
from .models import Pyme, Diagnostico, Brecha, Pregunta, PlantillaAccion, Accion


class BrechaInline(admin.TabularInline):
    model = Brecha
    extra = 0


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    inlines = [BrechaInline]


admin.site.register(Pyme)
admin.site.register(Pregunta)
admin.site.register(PlantillaAccion)
admin.site.register(Accion)