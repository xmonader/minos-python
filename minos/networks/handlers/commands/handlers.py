from __future__ import (
    annotations,
)

import logging
from inspect import (
    isawaitable,
)
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
    Tuple,
    Union,
)

from dependency_injector.wiring import (
    Provide,
    inject,
)

from minos.common import (
    Command,
    CommandStatus,
    MinosBroker,
    MinosConfig,
    MinosException,
)

from ...decorators import (
    EnrouteBuilder,
)
from ...messages import (
    Response,
    ResponseException,
)
from ..abc import (
    Handler,
)
from ..entries import (
    HandlerEntry,
)
from ..messages import (
    HandlerRequest,
)

logger = logging.getLogger(__name__)


class CommandHandler(Handler):
    """Command Handler class."""

    ENTRY_MODEL_CLS = Command

    @inject
    def __init__(self, broker: MinosBroker = Provide["command_reply_broker"], **kwargs: Any):
        super().__init__(**kwargs)
        self.broker = broker

    @classmethod
    def _from_config(cls, *args, config: MinosConfig, **kwargs) -> CommandHandler:
        handlers = cls._handlers_from_config(config)
        # noinspection PyProtectedMember
        return cls(handlers=handlers, **config.broker.queue._asdict(), **kwargs)

    @staticmethod
    def _handlers_from_config(config: MinosConfig) -> dict[str, Callable[[HandlerRequest], Awaitable]]:
        builder = EnrouteBuilder(config.commands.service, config.queries.service, config=config)
        decorators = builder.get_broker_command_query()
        handlers = {decorator.topic: fn for decorator, fn in decorators.items()}
        return handlers

    async def dispatch_one(self, entry: HandlerEntry[Command]) -> None:
        """Dispatch one row.

        :param entry: Entry to be dispatched.
        :return: This method does not return anything.
        """
        logger.info(f"Dispatching '{entry!s}'...")

        fn = self.get_callback(entry.callback)
        command = entry.data
        items, status = await fn(command)

        await self.broker.send(items, topic=command.reply_topic, saga=command.saga, status=status)

    @staticmethod
    def get_callback(
        fn: Callable[[HandlerRequest], Union[Optional[HandlerRequest], Awaitable[Optional[HandlerRequest]]]]
    ) -> Callable[[Command], Awaitable[Tuple[Any, CommandStatus]]]:
        """Get the handler function to be used by the Command Handler.

        :param fn: The action function.
        :return: A wrapper function around the given one that is compatible with the Command Handler API.
        """

        async def _fn(command: Command) -> Tuple[Any, CommandStatus]:
            try:
                request = HandlerRequest(command)
                response = fn(request)
                if isawaitable(response):
                    response = await response
                if isinstance(response, Response):
                    response = await response.content()
                return response, CommandStatus.SUCCESS
            except ResponseException as exc:
                logger.info(f"Raised a user exception: {exc!s}")
                return repr(exc), CommandStatus.ERROR
            except MinosException as exc:
                logger.warning(f"Raised a 'minos' exception: {exc!r}")
                return repr(exc), CommandStatus.SYSTEM_ERROR
            except Exception as exc:
                logger.exception(f"Raised an exception: {exc!r}.")
                return repr(exc), CommandStatus.SYSTEM_ERROR

        return _fn
