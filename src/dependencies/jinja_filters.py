from datetime import datetime
from urllib.parse import urlencode


def url_with_params(query_params, **new_params):
    params = dict(query_params)
    params.update(new_params)
    return "?" + urlencode(params)


def strptime_filter(date_string, format="%Y-%m-%d"):
    """Convert string to datetime object"""
    return datetime.strptime(date_string, format)


def strftime_filter(date_obj, format="%Y-%m-%d"):
    """Format datetime object as string"""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(format)
