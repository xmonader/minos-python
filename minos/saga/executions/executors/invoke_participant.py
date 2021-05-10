"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
import uuid
from typing import (
    Any,
)

from minos.common import (
    Aggregate,
)

from ..context import (
    SagaContext,
)
from .publish import (
    PublishExecutor,
)


class InvokeParticipantExecutor(PublishExecutor):
    """TODO"""

    def _run_callback(self, operation: dict[str, Any], context: SagaContext) -> Aggregate:
        return super().exec_one(operation, context)
