import datetime
import json
import rollbar
from time import mktime

from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.http import QueryDict

from htk.api.constants import *

class HtkJSONEncoder(serializers.json.DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            value = int(mktime(obj.timetuple()))
        else:
            try:
                value = super(HtkJSONEncoder, self).default(obj)
            except:
                rollbar.report_exc_info(extra_data={'obj': obj,})
                value = -3.14159 # return an absurd value so that we know the object wasn't serializable
        return value

def to_json(obj, encoder=HtkJSONEncoder):
    if hasattr(obj, '_meta'):
        if hasattr(obj, '__contains__'):
            return serializers.serialize('json', obj )
        else:
            return serializers.serialize('json', [ obj ])
    else:
        return json.dumps(obj, cls=encoder)

def json_okay():
    return { HTK_API_JSON_KEY_STATUS : HTK_API_JSON_VALUE_OKAY }

def json_error():
    return { HTK_API_JSON_KEY_STATUS : HTK_API_JSON_VALUE_ERROR }

def json_okay_str():
    return to_json(json_okay())

def json_error_str():
    return to_json(json_error())

def json_response(obj, encoder=HtkJSONEncoder, status=200):
    # TODO: consider the new django.http.response.JsonResponse in Django 1.7
    # https://docs.djangoproject.com/en/1.7/ref/request-response/
    response = HttpResponse(to_json(obj, encoder=encoder), content_type='application/json', status=status)
    return response

def json_response_okay():
    response = json_response(json_okay())
    return response

def json_response_error(data=None, status=400):
    if data is None:
        data = json_error()
    response = json_response(data, status=status)
    return response

def extract_post_params(post_data, expected_params, list_params=None, strict=True):
    """Extract `expected_params` from `post_data`

    Raise Exception if `strict` and any `expected_params` are missing
    """
    data = QueryDict(mutable=True)
    if list_params is None:
        list_params = []
    for param in expected_params:
        if strict and param not in post_data:
            raise Exception('Missing param: %s' % param)
        if param in list_params:
            value = post_data.getlist('%s[]' % param, False)
            if value is not False:
                value = json.dumps(value)
                data[param] = value
        else:
            value = post_data.get(param)
            if value is not None:
                data[param] = value
    return data
