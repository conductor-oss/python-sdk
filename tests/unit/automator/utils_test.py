import logging
import unittest
from dataclasses import dataclass
from typing import List

from requests.structures import CaseInsensitiveDict
from tests.unit.resources.workers import UserInfo

from conductor.client.automator.utils import convert_from_dict


@dataclass
class Address:
    street: str
    zip: str
    country: str


@dataclass
class UserDetails:
    name: str
    id: int
    address: List[Address]


class SubTest:

    def __init__(self, **kwargs) -> None:
        self.ba = kwargs.pop('ba')
        self.__dict__.update(kwargs)

    def printme(self):
        print(f'ba is: {self.ba} and all are {self.__dict__}')


class Test:

    def __init__(self, a, b: List[SubTest], d: list[UserInfo], g: CaseInsensitiveDict[str, UserInfo]) -> None:
        self.a = a
        self.b = b
        self.d = d
        self.g = g

    def do_something(self):
        print(f'a: {self.a}, b: {self.b}, typeof b: {type(self.b[0])}')
        print(f'd is {self.d}')


class TestTaskRunner(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_convert_non_dataclass(self):
        dictionary = {'a': 123, 'b': [{'ba': 2}, {'ba': 21}],
                      'd': [{'name': 'conductor', 'id': 123}, {'F': 3}],
                      'g': {'userA': {'name': 'userA', 'id': 100}, 'userB': {'name': 'userB', 'id': 101}}}
        value = convert_from_dict(Test, dictionary)
        self.assertEqual(Test, type(value))
        self.assertEqual(123, value.a)
        self.assertEqual(2, len(value.b))
        self.assertEqual(21, value.b[1].ba)
        self.assertEqual(SubTest, type(value.b[1]))

    def test_convert_dataclass(self):
        dictionary = {'name': 'user_a', 'id': 123,
                      'address': [{'street': '21 jump street', 'zip': '10101', 'country': 'USA'}]}
        value = convert_from_dict(UserDetails, dictionary)
        self.assertEqual(UserDetails, type(value), f'expected UserInfo, found {type(value)}')
