import json
from typing import Any, Dict

class JsonSerializer:
    """
    Narzędzie pomocnicze (Utility) zapewniające deterministyczną serializację.
    W blockchainie kolejność kluczy w JSON ma znaczenie dla hasha.
    """

    @staticmethod
    def serialize(obj: Any) -> str:
        """
        Konwertuje obiekt/słownik na deterministyczny string JSON.
        """
        # Jeśli obiekt ma metodę to_dict, użyj jej
        if hasattr(obj, 'to_dict'):
            data = obj.to_dict()
        elif hasattr(obj, '__dict__'):
            data = obj.__dict__
        else:
            data = obj

        # sort_keys=True jest krytyczne dla blockchaina!
        return json.dumps(data, sort_keys=True, indent=2)

    @staticmethod
    def deserialize(json_str: str) -> Dict[str, Any]:
        """
        Konwertuje string JSON na słownik.
        """
        return json.loads(json_str)
