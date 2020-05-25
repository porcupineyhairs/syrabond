from django.contrib import admin

from .models import *
from .appliences import *

admin.site.register(Resource)
admin.site.register(Tag)
admin.site.register(Group)
admin.site.register(Channel)
admin.site.register(Premise)
admin.site.register(State)
admin.site.register(Type)
admin.site.register(Facility)