import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from . import entities


class ImporterContext:
    def __init__(self) -> None:
        self._xml2entity = {}  # type: Dict[ET.Element,entities.Entity]
        self._xmlrefs = {}  # type: Dict[ET.Element,entities.Entity]

    def getref(self, xml: ET.Element) -> 'entities.Entity':
        if xml in self._xmlrefs:
            return self._xmlrefs[xml]
        else:
            return None

    def getentity(self, xml: ET.Element) -> 'entities.Entity':
        if xml in self._xml2entity:
            return self._xml2entity[xml]
        else:
            return None

    def setref(self, xml: ET.Element, entity: 'entities.Entity') -> None:
        self._xmlrefs[xml] = entity

    def setentity(self, xml: ET.Element, entity: 'entities.Entity') -> None:
        self._xml2entity[xml] = entity
