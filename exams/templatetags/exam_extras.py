from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Usage: {{ my_dict|get_item:key }} — looks up `key` in `dictionary`."""
    if not dictionary:
        return None
    return dictionary.get(key)
