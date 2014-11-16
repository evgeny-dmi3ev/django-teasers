from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.template import Context
from django.template.loader import get_template
from django.core.exceptions import ValidationError

from pytils.translit import slugify


class Block(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100,
        blank=True, unique=True)

    class Meta:
        verbose_name = _('Block')
        verbose_name_plural = _('Blocks')

    def __unicode__(self):
        return u"%s" % (self.name)

    def clean(self):
        if not self.slug:
            self.slug = slugify(self.name)

    def get_filters(self):
        filters = {}
        for f in self.filters.iterator():
            filters[f.name] = f.value
        return filters

    def get_teaser_ids(self, **f):
        ids = {}
        f.update(**self.get_filters())
        ctype_ids = self.templates.values_list('content_type', flat=True).distinct()
        for ctype in ContentType.objects.filter(pk__in=ctype_ids):
            filters = {}
            for field in ctype.fields.iterator():
                if field.name in f:
                    if f[field.name]=='magic:now':
                        from datetime import datetime
                        f[field.name] = datetime.today()
                    filters[field.field] = f[field.name]
            temp = ctype.model_class().objects.\
                filter(**filters).values_list('id', flat=True)
            if temp:
                ids[ctype] = temp
        return ids

    def update_teasers(self, content_type, ids):
        new_teasers = []
        filters = {'content_type': content_type, 'object_id__in': ids}
        for template in self.templates.iterator():
            filters.update({'template': template})
            for teaser in Teaser.objects.filter(**filters).iterator():
                if teaser.object_id in ids:
                    ids.remove(teaser.object_id)
                teaser.save()
            for id in ids:
                new_teasers.append(Teaser.objects.create(
                    content_type=content_type,
                    object_id=id,
                    template=template
                ))
        return new_teasers


class Template(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    content_type = models.ForeignKey(ContentType,
        verbose_name=_('content type'),)
    block = models.ForeignKey(Block, related_name='templates')

    class Meta:
        verbose_name = _('Template')
        verbose_name_plural = _('Templates')
        unique_together = ('content_type', 'block')

    def __unicode__(self):
        return u"%s" % (self.name)

    def save(self, *args, **kwargs):
        super(Template, self).save(*args, **kwargs)
        ids = list(self.content_type.model_class().objects.all().values_list('id', flat=True))
        for teaser in self.teasers.iterator():
            if teaser.object_id in ids:
                ids.remove(teaser.object_id)
            teaser.save()
        for id in ids:
            Teaser.objects.create(
                content_type=self.content_type,
                object_id=id,
                template=self
            )

    def clean(self):
        try:
            get_template(self.name)
        except:
            raise ValidationError(_('Template "%s" does not exist.' % self.name))


class Teaser(models.Model):
    content_type = models.ForeignKey(ContentType,
        verbose_name=_('content type'),)
    object_id = models.PositiveIntegerField(
        verbose_name=_('object id'), db_index=True,)
    content_object = generic.GenericForeignKey()
    template = models.ForeignKey(Template, related_name='teasers')
    rendered = models.TextField(_('Body'), null=True, blank=True)

    class Meta:
        verbose_name = _('Template')
        verbose_name_plural = _('Templates')
        unique_together = ('content_type', 'object_id', 'template')

    def __unicode__(self):
        return u"%s" % (self.rendered)

    def save(self, *args, **kwargs):
        template = get_template(self.template.name)
        self.rendered = template.render(Context({'object': self.content_object}))
        super(Teaser, self).save(*args, **kwargs)


class Field(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    content_type = models.ForeignKey(ContentType,
        verbose_name=_('content type'), related_name='fields')
    field = models.CharField(_('Field'), max_length=100)

    class Meta:
        verbose_name = _('Field')
        verbose_name_plural = _('Fields')
        unique_together = ('content_type', 'name')

    def __unicode__(self):
        return u"%s" % (self.name)


class Filter(models.Model):
    name = models.CharField(_('Name'), max_length=100)
    block = models.ForeignKey(Block, related_name='filters')
    value = models.CharField(_('Value'), max_length=100)

    class Meta:
        verbose_name = _('Filter')
        verbose_name_plural = _('Filters')
        unique_together = ('block', 'name')

    def __unicode__(self):
        return u"%s=%s" % (self.name, self.value)
