from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    return field.as_widget(attrs={"class": css})

'''
@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

'''

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def is_in(value, container):
    return value in container



@register.filter(name='highlight')
def highlight(text, search):
    if not search:
        return text
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    return pattern.sub(f'<mark>{search}</mark>', text)