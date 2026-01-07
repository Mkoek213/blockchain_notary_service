"""
Testy jednostkowe dla EventBus.
EventBus to część Blockchain Core - system komunikacji Pub-Sub dla modułów.
"""

from blockchain_core import EventBus, EventType


class TestEventBus:
    """Testy dla EventBus - pełna funkcjonalność systemu zdarzeń."""

    def setup_method(self):
        """Przygotowanie przed każdym testem."""
        self.event_bus = EventBus()

    def test_subscribe_and_publish(self):
        """Test podstawowej subskrypcji i publikacji."""
        # Given
        received = []

        def handler(data):
            received.append(data)

        self.event_bus.subscribe(EventType.BLOCK_MINED, handler)

        # When
        self.event_bus.publish(EventType.BLOCK_MINED, {"test": "data"})

        # Then
        assert len(received) == 1
        assert received[0]["test"] == "data"

    def test_multiple_subscribers_same_event(self):
        """Test wielu subskrybentów tego samego wydarzenia."""
        # Given
        received1 = []
        received2 = []

        self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: received1.append(d))
        self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: received2.append(d))

        # When
        self.event_bus.publish(EventType.BLOCK_MINED, {"value": 123})

        # Then
        assert len(received1) == 1
        assert len(received2) == 1
        assert received1[0] == received2[0]

    def test_unsubscribe(self):
        """Test odsubskrybowania."""
        # Given
        received = []
        sub_id = self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: received.append(d))

        # When
        self.event_bus.publish(EventType.BLOCK_MINED, {"msg": "1"})
        self.event_bus.unsubscribe(sub_id)
        self.event_bus.publish(EventType.BLOCK_MINED, {"msg": "2"})

        # Then
        assert len(received) == 1
        assert received[0]["msg"] == "1"

    def test_different_event_types_isolated(self):
        """Test izolacji różnych typów wydarzeń."""
        # Given
        block_mined = []
        block_received = []

        self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: block_mined.append(d))
        self.event_bus.subscribe(EventType.BLOCK_RECEIVED, lambda d: block_received.append(d))

        # When
        self.event_bus.publish(EventType.BLOCK_MINED, {"type": "mined"})
        self.event_bus.publish(EventType.BLOCK_RECEIVED, {"type": "received"})

        # Then
        assert len(block_mined) == 1
        assert len(block_received) == 1
        assert block_mined[0]["type"] == "mined"
        assert block_received[0]["type"] == "received"

    def test_publish_without_subscribers(self):
        """Test publikacji bez subskrybentów - nie powinno rzucać błędu."""
        # When/Then
        self.event_bus.publish(EventType.BLOCK_MINED, {"data": "test"})

    def test_subscribe_returns_unique_id(self):
        """Test zwracania unikalnych ID subskrypcji."""
        # Given/When
        id1 = self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: None)
        id2 = self.event_bus.subscribe(EventType.BLOCK_MINED, lambda d: None)
        id3 = self.event_bus.subscribe(EventType.BLOCK_RECEIVED, lambda d: None)

        # Then
        assert id1 != id2
        assert id2 != id3
        assert isinstance(id1, str)

    def test_multiple_publishes(self):
        """Test wielokrotnej publikacji."""
        # Given
        counter = [0]
        self.event_bus.subscribe(
            EventType.BLOCK_MINED, lambda d: counter.__setitem__(0, counter[0] + 1)
        )

        # When
        for _ in range(5):
            self.event_bus.publish(EventType.BLOCK_MINED, {})

        # Then
        assert counter[0] == 5

    def test_unsubscribe_nonexistent_id(self):
        """Test odsubskrybowania nieistniejącego ID."""
        # When
        result = self.event_bus.unsubscribe("nonexistent_id_12345")

        # Then - powinno zwrócić False lub nie rzucić wyjątku
        assert result is False or result is None

    def test_all_event_types_work(self):
        """Test że wszystkie typy EventType działają."""
        # Given
        counters = {}

        for event_type in [
            EventType.BLOCK_MINED,
            EventType.BLOCK_RECEIVED,
            EventType.TRANSACTION_RECEIVED,
            EventType.PEER_CONNECTED,
        ]:
            counters[event_type] = [0]
            self.event_bus.subscribe(
                event_type,
                lambda d, et=event_type: counters[et].__setitem__(0, counters[et][0] + 1),
            )

        # When
        for event_type in counters.keys():
            self.event_bus.publish(event_type, {})

        # Then
        for count in counters.values():
            assert count[0] == 1
