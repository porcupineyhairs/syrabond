from django.db import models
from django.contrib.postgres.fields import JSONField

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


class Type(BaseModel):

    title = models.CharField(verbose_name='Тип', max_length=100)
    key = models.CharField(verbose_name='код', max_length=50)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Тип устройства',
        verbose_name_plural = 'Типы устройств'


class Group(BaseModel):

    title = models.CharField(verbose_name='Группа', max_length=100)
    key = models.CharField(verbose_name='код', max_length=10)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Группа',
        verbose_name_plural = 'Группы'

class Channel(BaseModel):

    title = models.CharField(verbose_name='Канал', max_length=10)

    def __str__(self):
        return self.title

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
    title = models.CharField(verbose_name='Состояние', max_length=20)
    channel = models.ForeignKey(
        Channel,
        verbose_name='Канал',
        related_name='показания',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    current = models.CharField(verbose_name='Значение', max_length=20)

    def __str__(self):
        return f'{[res for res in self.resource.all()]}: {self.current}'

    class Meta:
        verbose_name = 'Статус',
        verbose_name_plural = 'Статусы'


class Resource(BaseModel):

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
        related_name='resources',
        blank=False,
        null=False,
        on_delete=models.CASCADE
    )

    type = models.ForeignKey(
        Type,
        verbose_name='Тип устройства',
        related_name='resources',
        blank=False,
        null=False,
        on_delete=models.CASCADE
    )

    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        related_name='resources',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    location = models.ForeignKey(
        Premise,
        verbose_name='Расположение',
        related_name='resources',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    state = models.ForeignKey(
        State,
        verbose_name='Состояние',
        related_name='resource',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        related_name='resources',
        blank=True
    )

    extra = JSONField(
        verbose_name='Прочее',
        blank=True,
        null=True
    )

    def __str__(self):
        return f'{self.title} {self.uid}'

    def __repr__(self):
        return str(self)

    class Meta:
        verbose_name = 'Устройство',
        verbose_name_plural = 'Устройства'
