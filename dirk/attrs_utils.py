import typing

import zope.interface
from attrs import resolve_types, validators


def field_transformer(namespace):
    def transform(cls, fields):
        results = []
        resolve_types(
            cls, globalns=namespace, localns={cls.__name__: cls}, attribs=fields
        )
        for field in fields:
            original_type = getattr(field.type, "__origin__", None)
            if type(field.type) is str and field.type == cls.__name__:
                field = field.evolve(type=cls)
            if type(field.type) is type:
                validator = validators.instance_of(field.type)
            elif type(field.type) is zope.interface.interface.InterfaceClass:
                validator = validators.provides(field.type)
            elif original_type is list or original_type is typing.List:
                if (
                    type(field.type.__args__[0])
                    is zope.interface.interface.InterfaceClass
                ):
                    validator = validators.deep_iterable(
                        member_validator=validators.provides(field.type.__args__[0])
                    )
                else:
                    validator = validators.deep_iterable(
                        member_validator=validators.instance_of(field.type.__args__[0])
                    )
            elif original_type is dict or original_type is typing.Dict:
                if (
                    type(field.type.__args__[1])
                    is zope.interface.interface.InterfaceClass
                ):
                    validator = validators.deep_mapping(
                        key_validator=validators.instance_of(field.type.__args__[0]),
                        value_validator=validators.provides(field.type.__args__[1]),
                    )
                else:
                    validator = validators.deep_mapping(
                        key_validator=validators.instance_of(field.type.__args__[0]),
                        value_validator=validators.instance_of(field.type.__args__[1]),
                    )
            else:
                raise TypeError(
                    "unanticipated type %s (%s)"
                    % (field.type, getattr(field.type, "__origin__"))
                )
            validator = validators.optional(validator)
            validator = (
                validator
                if field.validator is None
                else validators.and_(field.validator, validator)
            )
            results.append(field.evolve(default=None, validator=validator))
        return results

    return transform
