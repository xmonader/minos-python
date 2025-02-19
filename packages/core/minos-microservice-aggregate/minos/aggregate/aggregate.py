from __future__ import (
    annotations,
)

from typing import (
    Generic,
    TypeVar,
    get_args,
)

from dependency_injector.wiring import (
    Provide,
    inject,
)

from minos.common import (
    MinosConfig,
    MinosSetup,
    NotProvidedException,
)

from .entities import (
    RootEntity,
)
from .events import (
    EventRepository,
)
from .snapshots import (
    SnapshotRepository,
)
from .transactions import (
    TransactionRepository,
)

RT = TypeVar("RT", bound=RootEntity)


class Aggregate(Generic[RT], MinosSetup):
    """Base Service class"""

    transaction_repository: TransactionRepository
    event_repository: EventRepository
    snapshot_repository: SnapshotRepository

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        event_repository: EventRepository,
        snapshot_repository: SnapshotRepository,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._check_root()

        self.transaction_repository = transaction_repository
        self.event_repository = event_repository
        self.snapshot_repository = snapshot_repository

    @classmethod
    def _from_config(cls, config: MinosConfig, **kwargs) -> Aggregate:
        kwargs["transaction_repository"] = cls._get_transaction_repository(**kwargs)
        kwargs["event_repository"] = cls._get_event_repository(**kwargs)
        kwargs["snapshot_repository"] = cls._get_snapshot_repository(**kwargs)
        return cls(**kwargs)

    # noinspection PyUnusedLocal
    @staticmethod
    @inject
    def _get_transaction_repository(
        transaction_repository: TransactionRepository = Provide["transaction_repository"], **kwargs
    ) -> TransactionRepository:
        if transaction_repository is None or isinstance(transaction_repository, Provide):
            raise NotProvidedException(f"A {TransactionRepository!r} object must be provided.")
        return transaction_repository

    # noinspection PyUnusedLocal
    @staticmethod
    @inject
    def _get_event_repository(
        event_repository: EventRepository = Provide["event_repository"], **kwargs
    ) -> EventRepository:
        if event_repository is None or isinstance(event_repository, Provide):
            raise NotProvidedException(f"A {EventRepository!r} object must be provided.")
        return event_repository

    # noinspection PyUnusedLocal
    @staticmethod
    @inject
    def _get_snapshot_repository(
        snapshot_repository: SnapshotRepository = Provide["snapshot_repository"], **kwargs
    ) -> SnapshotRepository:
        if snapshot_repository is None or isinstance(snapshot_repository, Provide):
            raise NotProvidedException(f"A {SnapshotRepository!r} object must be provided.")
        return snapshot_repository

    def _check_root(self):
        self.root  # If root is not valid it will raise an exception.

    @property
    def root(self) -> type[RootEntity]:
        """Get the root entity of the aggregate.

        :return: A ``RootEntity`` type.
        """
        # noinspection PyUnresolvedReferences
        bases = self.__orig_bases__
        root = get_args(bases[0])[0]
        if not isinstance(root, type) or not issubclass(root, RootEntity):
            raise TypeError(f"{type(self)!r} must contain a {RootEntity!r} as generic value.")
        return root
