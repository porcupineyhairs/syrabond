from django.contrib import admin

from .models import *


def make_on(modeladmin, request, queryset):
    [n.on() for n in queryset]


def make_off(modeladmin, request, queryset):
    [n.off() for n in queryset]


def make_connect(modeladmin, request, queryset):
    [n.connect() for n in queryset]


class SwitchAdmin(admin.ModelAdmin):
    actions = [make_on, make_off]
    list_display = ('title', 'uid', 'state_')


class SensorAdmin(admin.ModelAdmin):
    actions = [make_connect]
    list_display = ('title', 'uid', 'state_')


admin.site.register(Switch, SwitchAdmin),
admin.site.register(Sensor, SensorAdmin),
admin.site.register(Tag)
admin.site.register(Group)
admin.site.register(Channel)
admin.site.register(Premise)
admin.site.register(State)
admin.site.register(Facility)
