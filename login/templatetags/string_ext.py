from django import template

register=template.Library()

def contains(value, checkstr):
    return checkstr.lower() in str(value).lower()

register.filter(contains)

def startswith(value, checkstr):
    return value.lower().startswith(checkstr.lower())

register.filter(startswith)