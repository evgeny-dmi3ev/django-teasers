from django import template
from django.contrib.contenttypes.models import ContentType
import random

from ..models import Block, Teaser, Template


register = template.Library()


@register.assignment_tag
def random_teasers(block_slug, *args, **kwargs):
    block = Block.objects.get(slug=block_slug)
    try:
        limit = int(block.filters.get(name__exact='limit').value)
    except:
        limit = kwargs.pop('limit', 3)

    teasers = []
    if block:
        pks = {}
        ids = block.get_teaser_ids(**kwargs)
        if ids:
            ctypes = ids.keys()
            for ctype in ctypes:
                if ids[ctype]:
                    tmp = list(ids[ctype])
                    random.shuffle(tmp)
                    pks[ctype] = tmp[:limit]
            for key, values in pks.items():
                tmp = list(Teaser.objects.filter(
                    content_type=key,
                    object_id__in=values,
                    template__block=block))
                teasers.extend(tmp)
                if len(tmp) < limit:
                    teasers.extend(block.update_teasers(key, values))
    random.shuffle(teasers)
    return teasers[:limit]

@register.assignment_tag
def teasers_for_objects(block_slug, objects, *args, **kwargs):
    limit = kwargs.get('limit', 3)

    block = Block.objects.get(slug=block_slug)
    teasers = []
    if block and objects:
        ids = [obj.id for obj in objects]
        ctype =  ContentType.objects.get_for_model(objects[0])
        teasers = list(Teaser.objects.filter(
                    content_type=ctype,
                    object_id__in=ids,
                    template__block=block)[:limit])
    return teasers
