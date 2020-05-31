
from django.contrib import admin
from django.db import models
from django.contrib.postgres.fields import JSONField

from .appliences import *


class BaseModel(models.Model):

    class Meta:
        abstract = True


class Facility(BaseModel):

    title = models.CharField(verbose_name='Объект', max_length=100)
    key = models.CharField(verbose_name='код', max_length=10)

    def __str__(self):
        return f'{self.title} {self.key}'

    class Meta:
        verbose_name = 'Объект',
        verbose_name_plural = 'Объекты'


class Group(BaseModel):

    title = models.CharField(verbose_name='Группа', max_length=100)
    key = models.CharField(verbose_name='код', max_length=10)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа',
        verbose_name_plural = 'Группы'


class Channel(BaseModel):

    key = models.CharField(verbose_name='Канал', max_length=10)

    def __str__(self):
        return self.key

    class Meta:
        verbose_name = 'Канал',
        verbose_name_plural = 'Каналы'


class Tag(BaseModel):

    title = models.CharField(verbose_name='Тэг', max_length=100)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тэг',
        verbose_name_plural = 'Тэги'


class Premise(BaseModel):

    title = models.CharField(verbose_name='Помещение', max_length=100)
    location = models.ForeignKey(
        'self',
        verbose_name='Местонахождение',
        related_name='nested',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.title} {self.location if self.location else ""}'

    class Meta:
        verbose_name = 'Местоположение',
        verbose_name_plural = 'Местоположения'


class State(BaseModel):

    data = JSONField(
        verbose_name='инфо',
        blank=True,
        null=True
    )
    current = models.CharField(
        verbose_name='Значение',
        max_length=20,
        null=True,
        blank=True
    )

    def __str__(self):
        return f'{self.current}'

    class Meta:
        verbose_name = 'Статус',
        verbose_name_plural = 'Статусы'


class Resource(BaseModel, ResourceApp):

    title = models.CharField(verbose_name='Название', max_length=100)
    uid = models.CharField(
        verbose_name='Идентификатор',
        max_length=50,
        blank=False,
        null=False,
        db_index=True
    )

    facility = models.ForeignKey(
        Facility,
        verbose_name='Объект',
        related_name="%(class)s_resources",
        blank=False,
        null=True,
        on_delete=models.CASCADE
    )

    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        related_name="%(class)s_resources",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    location = models.ForeignKey(
        Premise,
        verbose_name='Расположение',
        related_name="%(class)s_resources",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    state = models.OneToOneField(
        State,
        verbose_name='Состояние',
        related_name="%(class)s_resources",
        blank=True,
        null=True,
        editable=False,
        on_delete=models.CASCADE
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name="%(class)s_resources",
        blank=True
    )

    extra = JSONField(
        verbose_name='Прочее',
        blank=True,
        null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.state:
            self.state = State.objects.create()
            self.state.save()
            self.save()

    def __str__(self):
        return f'{self.title} {self.uid}'

    def __repr__(self):
        return str(self)

    @property
    def topic(self):
        return self.facility.key+'/'+self.type+'/'+self.uid

    @property
    def type(self):
        return self._meta.model_name

    class Meta:
        abstract = True
        verbose_name = 'Устройство',
        verbose_name_plural = 'Устройства'


class Switch(Resource, SwitchApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def state_(self):
        return self.state.current if self.state else ''
    state_.short_description = 'Состояние'

    class Meta:
        verbose_name = 'Выключатель',
        verbose_name_plural = 'Выключатели'


class Sensor(SensorApp, Resource):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def state_(self):
        return self.state.data if self.state else ''
    state_.short_description = 'Показания'

    class Meta:
        verbose_name = 'Датчик',
        verbose_name_plural = 'Датчики'
