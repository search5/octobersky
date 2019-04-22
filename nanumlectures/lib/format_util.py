def date_format(value, format=None):
    if not value:
        return ''
    return value.strftime(format)
