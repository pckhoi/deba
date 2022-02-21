from unittest import TestCase
import typing

from attrs import define, field

import zope.interface
from deba.attrs_utils import field_transformer


class IC(zope.interface.Interface):
    def get_c():
        """get c"""


@define(field_transformer=field_transformer(globals()))
class A:
    a: str
    b: int
    c: typing.Union[str, typing.List[str]]
    d: float = field(default=3.14)


@zope.interface.implementer(IC)
@define(field_transformer=field_transformer(globals()))
class C:
    c: int

    def get_c(self):
        return self.c


@define(field_transformer=field_transformer(globals()))
class B:
    a: A
    b: typing.List[A]
    c: typing.Dict[str, A]
    d: IC
    e: typing.List[IC]
    f: typing.Dict[str, IC]


class FieldTransformerTestCase(TestCase):
    def test_scalar_fields(self):
        obj = A()
        self.assertIsNone(obj.a)
        self.assertIsNone(obj.b)
        self.assertEqual(obj.d, 3.14)

        obj = A("a", 1, d=12.3)
        self.assertEqual(obj.a, "a")
        self.assertEqual(obj.b, 1)
        self.assertEqual(obj.d, 12.3)

        with self.assertRaises(TypeError):
            obj = A(a=3)
        with self.assertRaises(TypeError):
            obj = A(b="3")

    def test_union_fields(self):
        obj = A(c="3")
        self.assertEqual(obj.c, "3")

        obj = A(c=["3"])
        self.assertEqual(obj.c, ["3"])

        with self.assertRaises(TypeError):
            obj = A(c=3.1)

    def test_nested_fields(self):
        obj = B()
        self.assertIsNone(obj.a)
        self.assertIsNone(obj.b)
        self.assertIsNone(obj.c)

        obj = B(a=A(), b=[], c=dict())
        self.assertEqual(obj.a, A())
        self.assertEqual(obj.b, [])
        self.assertEqual(obj.c, dict())

        obj = B(b=[A()], c={"a": A()})
        self.assertEqual(obj.b, [A()])
        self.assertEqual(obj.c, {"a": A()})

        with self.assertRaises(TypeError):
            obj = B(a=B())
        with self.assertRaises(TypeError):
            obj = B(b=A())
        with self.assertRaises(TypeError):
            obj = B(b=[B()])
        with self.assertRaises(TypeError):
            obj = B(c=A())
        with self.assertRaises(TypeError):
            obj = B(c={"a": B()})

    def test_interface_fields(self):
        obj = B(d=C())
        self.assertEqual(obj.d, C())
        with self.assertRaises(TypeError):
            obj = B(d=A())

        obj = B(e=[C()])
        self.assertEqual(obj.e, [C()])
        with self.assertRaises(TypeError):
            obj = B(e=[A()])

        obj = B(f={"a": C()})
        self.assertEqual(obj.f, {"a": C()})
        with self.assertRaises(TypeError):
            obj = B(f={"a": A()})
