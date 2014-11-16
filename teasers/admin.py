from django.contrib import admin
from django import forms
from django.contrib.contenttypes.models import ContentType
from .models import Block, Template, Field, Filter


class FilterForm(forms.ModelForm):
    class Meta:
        model = Filter

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)
        choices = (('', '--------'),('limit', 'limit'))
        for field in Field.objects.values_list('name', flat=True).distinct():
            choices += ((field, field),)
        self.fields['name'].widget = forms.Select(choices=choices)


class FilterInline(admin.options.InlineModelAdmin):
    fields = ('name', 'value')
    model = Filter
    fk_name = 'block'
    template = 'teasers/admin/inline.html'
    extra = 1
    form = FilterForm


class BlockAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    inlines = [FilterInline,]


class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'block']


class FieldAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'field']


admin.site.register(Block, BlockAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Field, FieldAdmin)

def update_teasers(self, request, queryset):
    model = queryset.model
    models = model._meta.parents.keys()
    models.append(model)
    ctypes = []
    for ctype in ContentType.objects.get_for_models(*models).values():
        ctypes.append(ctype.pk)
    ids = queryset.values_list('pk', flat=True)
    for block in Block.objects.filter(templates__content_type__in=ctypes).distinct():
        block.update_teasers(ctype, list(ids))
update_teasers.short_description = "Update teasers"

admin.site.add_action(update_teasers)


