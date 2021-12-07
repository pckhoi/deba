import re
import typing

import attr
import yaml


def to_camel_case(s):
    components = s.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


word_break_pattern = re.compile(r'([a-z])([A-Z])')


def to_snake_case(s):
    return word_break_pattern.sub(r'\1_\2', s).lower()


class _YAMLDumper(yaml.Dumper):
    def represent_object(self, data):
        if attr.has(data.__class__):
            fields = attr.fields(data.__class__)
            return self.represent_dict({
                to_camel_case(field.name): getattr(data, field.name)
                for field in fields if getattr(data, field.name) is not None
            })
        return super().represent_object(data)


def yaml_dump(data, **kwargs):
    return yaml.dump(data, Dumper=_YAMLDumper, **kwargs)


def yaml_load(s, serializer_cls):
    data = yaml.load(s)
    return _deserialize(data, serializer_cls)


def _deserialize(data, serializer_cls):
    kwargs = dict()
    fields_dict = attr.fields_dict(serializer_cls)
    data = [
        (to_snake_case(k), v) for k, v in data.items()
    ]
    data_stack = [
        (kwargs, k, fields_dict[k], v)
        for k, v in data if k != 'meta'
    ]
    while len(data_stack) > 0:
        parent, name, field, value = data_stack.pop()
        if type(field.type) is type:
            if attr.has(field.type):
                parent[name] = _deserialize(value, field.type)
            else:
                parent[name] = value
        elif field.type.__origin__ is list or field.type.__origin__ is typing.List:
            el_cls = field.type.__args__[0]
            if type(value) is not list:
                raise TypeError(
                    'keyword argument "%s" should be a list of %s' % (name, el_cls))
            if attr.has(el_cls):
                parent[name] = [
                    _deserialize(e, el_cls) for e in value
                ]
            else:
                parent[name] = value
        elif field.type.__origin__ is dict or field.type.__origin__ is typing.Dict:
            el_cls = field.type.__args__[1]
            if type(value) is not dict:
                raise TypeError(
                    'keyword argument "%s" should be a dict of %s' % (
                        name, el_cls)
                )
            if attr.has(el_cls):
                parent[name] = {
                    k: _deserialize(e, el_cls) for k, e in value.items()
                }
            else:
                parent[name] = value
        else:
            raise TypeError('unanticipated field type %s' % field.type)
    return serializer_cls(**kwargs)
