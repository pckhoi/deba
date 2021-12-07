import attr
import zope.interface

from liner.repositories import base


@zope.interface.implementer(base.Repository)
@attr.s(auto_attribs=True)
class WrglRepository(object):
    pass
