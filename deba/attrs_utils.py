import typing

import zope.interface
from attrs import resolve_types, validators, field, NOTHING, setters


def _union_type_validator(types):
    validators = tuple(_type_validator(t) for t in types)

    def check(self, attribute, value):
        for validate in validators:
            try:
                validate(self, attribute, value)
            except TypeError as e:
                pass
            else:
                return
        raise TypeError(
            "%s (%s) is not one of types: %s"
            % (value, type(value), ", ".join("%s" % t for t in types))
        )

    return check


def _type_validator(t):
    original_type = getattr(t, "__origin__", None)
    if type(t) is type:
        return validators.instance_of(t)
    elif type(t) is zope.interface.interface.InterfaceClass:
        return validators.provides(t)
    elif original_type is list or original_type is typing.List:
        return validators.deep_iterable(member_validator=_type_validator(t.__args__[0]))
    elif original_type is dict or original_type is typing.Dict:
        return validators.deep_mapping(
            key_validator=_type_validator(t.__args__[0]),
            value_validator=_type_validator(t.__args__[1]),
        )
    elif original_type is typing.Union:
        return _union_type_validator(t.__args__)
    raise TypeError("unanticipated type %s (%s)" % (t, getattr(t, "__origin__")))


def field_transformer(namespace):
    def transform(cls, fields):
        results = []
        resolve_types(
            cls, globalns=namespace, localns={cls.__name__: cls}, attribs=fields
        )
        for field in fields:
            if type(field.type) is str and field.type == cls.__name__:
                field = field.evolve(type=cls)
            validator = _type_validator(field.type)
            validator = (
                validator
                if field.validator is None
                else validators.and_(validator, field.validator)
            )
            if field.default is NOTHING and not field.metadata.get(REQUIRED_K, False):
                validator = validators.optional(validator)
                field = field.evolve(default=None)
            on_setattr = setters.validate
            on_setattr = (
                on_setattr
                if field.on_setattr is None
                else setters.pipe(on_setattr, field.on_setattr)
            )
            results.append(field.evolve(validator=validator, on_setattr=on_setattr))
        return results

    return transform


DOC_K = "deba_doc"
REQUIRED_K = "deba_required"


def doc(
    doc: str,
    default=NOTHING,
    factory=None,
    converter=None,
    required=False,
    validator=None,
):
    return field(
        metadata={DOC_K: doc, REQUIRED_K: required},
        default=default,
        factory=factory,
        converter=converter,
        validator=validator,
    )
