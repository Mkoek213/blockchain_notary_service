"""
Prosty Event Bus dla komunikacji między modułami (wzorzec Publish-Subscribe).

Zgodnie z sekcją 7 dokumentacji - system zdarzeń umożliwia
asynchroniczną komunikację między modułami bez ścisłego sprzężenia.
"""

import uuid
from typing import Any, Callable, Dict, List

from .interfaces_extended import EventType, IEventBus


class EventBus(IEventBus):
    """
    Implementacja Event Bus (wzorzec Pub-Sub).

    Przykład użycia:

    # Inicjalizacja
    event_bus = EventBus()

    # Subskrypcja
    def on_block_mined(payload):
        print(f"Nowy blok: {payload['block'].get_hash()}")

    sub_id = event_bus.subscribe(EventType.BLOCK_MINED, on_block_mined)

    # Publikacja
    event_bus.publish(EventType.BLOCK_MINED, {"block": new_block})

    # Anulowanie subskrypcji
    event_bus.unsubscribe(sub_id)
    """

    def __init__(self):
        """Inicjalizuje Event Bus z pustą mapą subskrypcji."""
        # Mapa: EventType -> Lista (subscription_id, handler)
        self._subscribers: Dict[EventType, List[tuple[str, Callable]]] = {}

        # Inicjalizuj puste listy dla wszystkich typów zdarzeń
        for event_type in EventType:
            self._subscribers[event_type] = []

    def publish(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """
        Publikuje zdarzenie do wszystkich subskrybentów.

        Args:
            event_type: Typ zdarzenia
            payload: Dane zdarzenia (dowolny dict)

        Przykład:
            event_bus.publish(EventType.BLOCK_MINED, {
                "block": new_block,
                "miner": "node_1"
            })
        """
        if event_type not in self._subscribers:
            return

        # Wywołaj wszystkich handlerow dla tego typu zdarzenia
        for subscription_id, handler in self._subscribers[event_type]:
            try:
                handler(payload)
            except Exception as e:
                # W produkcji można dodać logging
                print(f"Error in event handler {subscription_id}: {e}")

    def subscribe(self, event_type: EventType, handler: Callable[[Dict[str, Any]], None]) -> str:
        """
        Subskrybuje zdarzenie.

        Args:
            event_type: Typ zdarzenia do subskrypcji
            handler: Funkcja obsługująca zdarzenie (przyjmuje dict)

        Returns:
            ID subskrypcji (UUID) - użyj do późniejszego unsubscribe

        Przykład:
            def on_block_received(payload):
                block = payload["block"]
                peer = payload["peer_id"]
                print(f"Otrzymano blok {block.get_hash()} od {peer}")

            sub_id = event_bus.subscribe(
                EventType.BLOCK_RECEIVED,
                on_block_received
            )
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        # Generuj unikalny ID subskrypcji
        subscription_id = str(uuid.uuid4())

        # Dodaj handler do listy
        self._subscribers[event_type].append((subscription_id, handler))

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Usuwa subskrypcję.

        Args:
            subscription_id: ID subskrypcji (zwrócony przez subscribe)

        Returns:
            True jeśli subskrypcja została usunięta, False jeśli nie znaleziono

        Przykład:
            sub_id = event_bus.subscribe(EventType.BLOCK_MINED, handler)
            # ... później ...
            event_bus.unsubscribe(sub_id)
        """
        for event_type, subscribers in self._subscribers.items():
            # Znajdź subskrypcję po ID
            for i, (sub_id, handler) in enumerate(subscribers):
                if sub_id == subscription_id:
                    # Usuń z listy
                    self._subscribers[event_type].pop(i)
                    return True

        return False

    def get_subscriber_count(self, event_type: EventType) -> int:
        """
        Zwraca liczbę subskrybentów dla danego typu zdarzenia.

        Args:
            event_type: Typ zdarzenia

        Returns:
            Liczba aktywnych subskrypcji
        """
        if event_type not in self._subscribers:
            return 0
        return len(self._subscribers[event_type])

    def clear_all_subscriptions(self) -> None:
        """
        Usuwa wszystkie subskrypcje.
        Przydatne przy testach lub shutdownie aplikacji.
        """
        for event_type in EventType:
            self._subscribers[event_type] = []
