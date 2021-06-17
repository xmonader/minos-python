"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
from __future__ import (
    annotations,
)

import logging
import typing as t
from itertools import (
    zip_longest,
)

from ...meta import (
    self_or_classmethod,
)
from ..abc import (
    Model,
)
from ..fields import (
    ModelField,
)
from ..types import (
    MissingSentinel,
)

logger = logging.getLogger(__name__)

T = t.TypeVar("T")


class DeclarativeModel(Model, t.Generic[T]):
    """Base class for ``minos`` declarative model entities."""

    def __init__(self, *args, **kwargs):
        """Class constructor.

        :param kwargs: Named arguments to be set as model attributes.
        """
        super().__init__()
        self._list_fields(*args, **kwargs)

    @classmethod
    def from_model_type(cls, model_type, data):
        """Build a ``DataTransferObject`` from a ``ModelType`` and ``data``.

        :param model_type: ``ModelType`` object containing the DTO's structure
        :param data: A dictionary containing the values to be stored on the DTO.
        :return: A new ``DataTransferObject`` instance.
        """
        return cls(**data)

    def _list_fields(self, *args, **kwargs) -> t.NoReturn:
        for (name, type_val), value in zip_longest(self._type_hints(), args, fillvalue=MissingSentinel):
            if name in kwargs and value is not MissingSentinel:
                raise TypeError(f"got multiple values for argument {repr(name)}")

            if value is MissingSentinel and name in kwargs:
                value = kwargs[name]

            self._fields[name] = ModelField(
                name, type_val, value, getattr(self, f"parse_{name}", None), getattr(self, f"validate_{name}", None)
            )

    # noinspection PyMethodParameters
    @self_or_classmethod
    def _type_hints(self_or_cls) -> dict[str, t.Any]:
        fields = dict()
        if isinstance(self_or_cls, type):
            cls = self_or_cls
        else:
            cls = type(self_or_cls)
        for b in cls.__mro__[::-1]:
            base_fields = getattr(b, "_fields", None)
            if base_fields is not None:
                list_fields = {k: v for k, v in t.get_type_hints(b).items() if not k.startswith("_")}
                fields |= list_fields
        logger.debug(f"The obtained fields are: {fields!r}")
        fields |= super()._type_hints()
        yield from fields.items()


MinosModel = DeclarativeModel
