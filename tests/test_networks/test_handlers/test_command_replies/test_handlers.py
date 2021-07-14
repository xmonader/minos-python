import unittest
from datetime import datetime
from uuid import uuid4

from minos.common import (
    CommandReply,
    CommandStatus,
)
from minos.common.testing import PostgresAsyncTestCase
from minos.networks import (
    CommandReplyHandler,
    HandlerEntry,
)
from tests.utils import (
    BASE_PATH,
    FakeModel,
    FakeSagaManager,
)


class TestCommandReplyHandler(PostgresAsyncTestCase):
    CONFIG_FILE_PATH = BASE_PATH / "test_config.yml"

    def test_from_config(self):
        saga_manager = FakeSagaManager()
        handler = CommandReplyHandler.from_config(config=self.config, saga_manager=saga_manager)
        self.assertIsInstance(handler, CommandReplyHandler)
        handlers = {"AddOrderReply": None, "DeleteOrderReply": None, "OrderQueryReply": None}
        self.assertEqual(handlers, handler.handlers)
        self.assertEqual(self.config.saga.queue.records, handler._records)
        self.assertEqual(self.config.saga.queue.retry, handler._retry)
        self.assertEqual(self.config.saga.queue.host, handler.host)
        self.assertEqual(self.config.saga.queue.port, handler.port)
        self.assertEqual(self.config.saga.queue.database, handler.database)
        self.assertEqual(self.config.saga.queue.user, handler.user)
        self.assertEqual(self.config.saga.queue.password, handler.password)
        self.assertEqual(saga_manager, handler.saga_manager)

    def test_entry_model_cls(self):
        self.assertEqual(CommandReply, CommandReplyHandler.ENTRY_MODEL_CLS)

    async def test_dispatch(self):
        saga_manager = FakeSagaManager()
        saga = uuid4()
        command = CommandReply("TicketAdded", [FakeModel("foo")], saga, CommandStatus.SUCCESS)
        entry = HandlerEntry(1, "TicketAdded", None, 0, command, 1, datetime.now())

        async with CommandReplyHandler.from_config(config=self.config, saga_manager=saga_manager) as handler:
            await handler.dispatch_one(entry)

        self.assertEqual(None, saga_manager.name)
        self.assertEqual(command, saga_manager.reply)


if __name__ == "__main__":
    unittest.main()
