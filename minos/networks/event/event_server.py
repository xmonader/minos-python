# Copyright (C) 2020 Clariteia SL
#
# This file is part of minos framework.
#
# Minos framework can not be copied and/or distributed without the express
# permission of Clariteia SL.

from __future__ import annotations

import asyncio
import datetime
from typing import (
    NoReturn,
    Optional,
    Awaitable,
    Any,
    AsyncIterator,
)

import aiopg

from minos.common.broker import Event
from minos.common.configuration.config import MinosConfig
from minos.common.logs import log
from minos.networks.exceptions import MinosNetworkException
from .abc import MinosEventSetup


class MinosEventServer(MinosEventSetup):
    """
    Event Manager

    Consumer for the Broker ( at the moment only Kafka is supported )

    """

    __slots__ = "_tasks", "_db_dsn", "_handlers", "_topics", "_kafka_conn_data", "_broker_group_name"

    def __init__(self, *, config: MinosConfig, **kwargs: Any):
        super().__init__(**kwargs, **config.events.queue._asdict())
        self._tasks = set()  # type: t.Set[asyncio.Task]
        self._db_dsn = (
            f"dbname={config.events.queue.database} user={config.events.queue.user} "
            f"password={config.events.queue.password} host={config.events.queue.host}"
        )
        self._handler = {
            item.name: {"controller": item.controller, "action": item.action} for item in config.events.items
        }
        self._topics = list(self._handler.keys())
        self._kafka_conn_data = f"{config.events.broker.host}:{config.events.broker.port}"
        self._broker_group_name = f"event_{config.service.name}"

    @classmethod
    def from_config(cls, *args, config: MinosConfig = None, **kwargs) -> Optional[MinosEventServer]:
        """Build a new repository from config.
        :param args: Additional positional arguments.
        :param config: Config instance. If `None` is provided, default config is chosen.
        :param kwargs: Additional named arguments.
        :return: A `MinosRepository` instance.
        """
        if config is None:
            config = MinosConfig.get_default()
        if config is None:
            return None
        # noinspection PyProtectedMember
        return cls(*args, config=config, **kwargs)

    async def event_queue_add(self, topic: str, partition: int, binary: bytes):
        """Insert row to event_queue table.

        Retrieves number of affected rows and row ID.

        Args:
            topic: Kafka topic. Example: "TicketAdded"
            partition: Kafka partition number.
            binary: Event Model in bytes.

        Returns:
            Affected rows and queue ID.

            Example: 1, 12

        Raises:
            Exception: An error occurred inserting record.
        """

        async with aiopg.create_pool(self._db_dsn) as pool:
            async with pool.acquire() as connect:
                async with connect.cursor() as cur:
                    await cur.execute(
                        "INSERT INTO event_queue (topic, partition_id, binary_data, creation_date) VALUES (%s, %s, %s, %s) RETURNING id;",
                        (topic, partition, binary, datetime.datetime.now(),),
                    )

                    queue_id = await cur.fetchone()
                    affected_rows = cur.rowcount

        return affected_rows, queue_id[0]

    async def handle_single_message(self, msg):
        """Handle Kafka messages.

        Evaluate if the binary of message is an Event instance.
        Add Event instance to the event_queue table.

        Args:
            msg: Kafka message.

        Raises:
            Exception: An error occurred inserting record.
        """
        # the handler receive a message and store in the queue database
        # check if the event binary string is well formatted
        if not self._is_valid_event(msg.value):
            return
        affected_rows, id = await self.event_queue_add(msg.topic, msg.partition, msg.value)
        return affected_rows, id

    def _is_valid_event(self, value: bytes):
        try:
            Event.from_avro_bytes(value)
            return True
        except:
            return False

    async def handle_message(self, consumer: AsyncIterator):
        """Message consumer.

        It consumes the messages and sends them for processing.

        Args:
            consumer: Kafka Consumer instance (at the moment only Kafka consumer is supported).
        """

        async for msg in consumer:
            await self.handle_single_message(msg)
