"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""

from __future__ import (
    annotations,
)

import asyncio
from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
    Optional,
)

from ..exceptions import (
    MinosAlreadyOnSagaException,
)
from .abc import (
    MinosBaseSagaBuilder,
)
from .step import (
    SagaStep,
)

if TYPE_CHECKING:
    from ..executions import (
        SagaExecution,
    )


class Saga(MinosBaseSagaBuilder):
    """TODO"""

    def __init__(self, name, loop: asyncio.AbstractEventLoop = None, steps: list[SagaStep] = None):
        if steps is None:
            steps = list()

        self.name = name
        self.loop = loop or asyncio.get_event_loop()
        self.steps = steps

    def step(self, step: Optional[SagaStep] = None) -> SagaStep:
        """TODO

        :return: TODO
        """
        if step is None:
            step = SagaStep(self)
        else:
            if step.saga is not None:
                raise MinosAlreadyOnSagaException()
            step.saga = self

        self.steps.append(step)
        return step

    def build_execution(self, *args, **kwargs) -> SagaExecution:
        """TODO

        :return: TODO
        """
        from ..executions import (
            SagaExecution,
        )

        return SagaExecution.from_saga(self, *args, **kwargs)

    @property
    def raw(self) -> dict[str, Any]:
        """TODO

        :return: TODO
        """
        return {
            "name": self.name,
            "steps": [step.raw for step in self.steps],
        }
