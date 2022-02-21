# SPDX-License-Identifier: Apache-2.0
# Copyright © 2021 Wrangle Ltd

import typing
from unittest import TestCase

from attrs import define, field

from deba.serialize import yaml_load, yaml_dump


@define()
class Person(object):
    name: str = field(default=None)
    birth_date: str = field(default=None)
    height: int = field(default=None)
    scores: typing.List[int] = field(default=None)
    _gender: str = field(default=None)


@define()
class Website(object):
    url: str = field(default=None)


@define()
class Employment(object):
    title: str = field(default=None)


@define()
class Listing(object):
    user: Person = field(default=None)
    websites: typing.List[Website] = field(default=None)
    employments: typing.Dict[str, Employment] = field(default=None)


@define()
class Animal(object):
    omnivore: bool = field(default=None)
    vertebrate: bool = field(default=None)


class YAMLTestCase(TestCase):
    def test_loads_simple(self):
        obj1 = Person(
            name="John Doe", birth_date="10/02/2000", height=170, scores=[7, 8, 9]
        )
        obj1._gender = "male"
        yaml_str = yaml_dump(obj1)
        self.assertEqual(
            yaml_str,
            "\n".join(
                [
                    "birthDate: 10/02/2000",
                    "height: 170",
                    "name: John Doe",
                    "scores:",
                    "- 7",
                    "- 8",
                    "- 9",
                    "",
                ]
            ),
        )
        obj2 = yaml_load(yaml_str, Person)
        self.assertIsNone(obj2._gender)
        obj1._gender = None
        self.assertEqual(obj1, obj2)

    def test_loads_nested(self):
        self.maxDiff = None
        obj1 = Listing(
            user=Person(name="John Doe", birth_date="10/02/2000", height=170),
            websites=[
                Website(url="https://url1"),
                Website(url="https://url2"),
            ],
            employments={
                "ABC": Employment(title="engineer"),
                "DEF": Employment(title="head QA"),
            },
        )
        yaml_str = yaml_dump(obj1, indent=4)
        self.assertEqual(
            yaml_str,
            "\n".join(
                [
                    "employments:",
                    "    ABC:",
                    "        title: engineer",
                    "    DEF:",
                    "        title: head QA",
                    "user:",
                    "    birthDate: 10/02/2000",
                    "    height: 170",
                    "    name: John Doe",
                    "websites:",
                    "-   url: https://url1",
                    "-   url: https://url2",
                    "",
                ]
            ),
        )
        obj2 = yaml_load(yaml_str, Listing)
        self.assertEqual(obj1, obj2)

    def test_loads_ignore_empty(self):
        obj = yaml_load('{"omnivore": true}', Animal)
        self.assertEqual(obj, Animal(omnivore=True))
