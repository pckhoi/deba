import re
import typing

import attr
import yaml
from yaml.dumper import Dumper


def to_camel_case(s):
    components = s.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


word_break_pattern = re.compile(r"([a-z])([A-Z])")


def to_snake_case(s):
    return word_break_pattern.sub(r"\1_\2", s).lower()


def noop(self, *args, **kw):
    pass


yaml.emitter.Emitter.process_tag = noop


def _object_as_dict(obj):
    if attr.has(obj.__class__):
        if hasattr(obj, "as_dict"):
            return obj.as_dict()
        fields = attr.fields(obj.__class__)
        return {
            to_camel_case(field.name): _object_as_dict(getattr(obj, field.name))
            for field in fields
            if not field.name.startswith("_")
            and getattr(obj, field.name, None) is not None
        }
    return obj


def represent_attr_object(dumper, data):
    if attr.has(data.__class__):
        return dumper.represent_dict(_object_as_dict(data))
    return dumper.represent_object(data)


yaml.add_multi_representer(object, represent_attr_object)


def yaml_dump(data, **kwargs) -> str:
    return yaml.dump(data, Dumper=Dumper, **kwargs)


def yaml_load(s, serializer_cls):
    data = yaml.load(s, Loader=yaml.Loader)
    return _deserialize(data, serializer_cls)


def _deserialize(data, serializer_cls):
    kwargs = dict()
    fields_dict = attr.fields_dict(serializer_cls)
    if type(data) is str:
        return serializer_cls.from_str(data)
    data = [(to_snake_case(k), v) for k, v in data.items()]
    data_stack = [(kwargs, k, fields_dict[k], v) for k, v in data if k != "meta"]
    while len(data_stack) > 0:
        parent, name, field, value = data_stack.pop()
        if value is None:
            parent[name] = value
        elif type(field.type) is type:
            if attr.has(field.type):
                parent[name] = _deserialize(value, field.type)
            else:
                parent[name] = value
        elif field.type.__origin__ is list or field.type.__origin__ is typing.List:
            el_cls = field.type.__args__[0]
            if type(value) is not list:
                raise TypeError(
                    'keyword argument "%s" should be a list of %s' % (name, el_cls)
                )
            if attr.has(el_cls):
                parent[name] = [_deserialize(e, el_cls) for e in value]
            else:
                parent[name] = value
        elif field.type.__origin__ is dict or field.type.__origin__ is typing.Dict:
            el_cls = field.type.__args__[1]
            if type(value) is not dict:
                raise TypeError(
                    'keyword argument "%s" should be a dict of %s' % (name, el_cls)
                )
            if attr.has(el_cls):
                parent[name] = {k: _deserialize(e, el_cls) for k, e in value.items()}
            else:
                parent[name] = value
        else:
            raise TypeError("unanticipated field type %s" % field.type)
    return serializer_cls(**kwargs)
