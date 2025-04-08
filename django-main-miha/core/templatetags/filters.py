from django import template

register = template.Library()

@register.filter(name='zero')
def zero(value):
    if len(str(value)) == 3:
        return value
    elif len(str(value)) == 2:
        return '0' + str(value)
    elif len(str(value)) == 1:
        return '00' + str(value)

@register.filter(name='zero2')
def zero(value):
    if len(str(value)) == 1:
        return '0' + str(value)
    return value

@register.filter(name='nones')
def nones(value):
    if value==None:
        return ''
    return value

@register.filter(name='iter')
def iter(value):
    if value==1:
        return range(1,1)
    elif value<=10:
        return range(1, value+1)
    else:
        return range(value-10, value+1)



@register.filter(name='reduce')
def reduce(value):
    return value - 1

@register.filter
def addclass(field,css):
    return field.as_widget(attrs={'class':css})