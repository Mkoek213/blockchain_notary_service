from typing import Any
# Import warunkowy/lokalny żeby uniknąć cyklicznych zależności przy imporcie w czasie definicji,
# jeśli Block też będzie importować coś z security.
# Zakładamy, że Block jest w blockchain_core.block_builder (gdzie jest zdefiniowany w kodzie)
# Ale Block jest w blockchain_core.block_builder.
# W Pythonie najlepiej używać TYPE_CHECKING do type hintów.

from .identity_manager import IdentityManager

class BlockSigner:
    """
    Klasa odpowiedzialna za podpisywanie bloków przy użyciu tożsamości węzła.
    """
    
    def __init__(self, identity_manager: IdentityManager):
        self.identity_manager = identity_manager

    def sign_block(self, block: Any) -> Any:
        """
        Podpisuje blok.
        Przyjmuje obiekt Block (duck typing lub import), podpisuje go i zwraca.
        """
        # Pobieramy dane do podpisu z bloku
        # Zakładamy że Block ma metodę _get_signable_data() lub podobną,
        # ale Block w obecnym kodzie używa ICryptoService wewnątrz sign_block.
        # Tutaj, zgodnie z diagramem, BlockSigner robi to "z zewnątrz" lub
        # deleguje.
        
        # Podejście 1: BlockSigner wywołuje block.sign_block(...) podając adapter.
        # Podejście 2: BlockSigner sam bierze dane, podpisuje i ustawia w bloku.
        
        # Zgodnie z diagramem: signBlock(block: Block) : Block
        # Zaimplementujmy to tak, że BlockSigner ręcznie podpisuje.
        
        # Musimy uzyskać dane do podpisu. 
        # W obecnej klasie Block jest metoda _get_signable_data (prywatna konwencja)
        # albo block.get_json_data().
        # Użyjmy publicznego API jeśli dostępne, lub _get_signable_data jeśli musimy.
        # W Pythonie _ jest dostępne.
        
        signable_data_dict = block._get_signable_data()
        
        # Serializacja do bytes (musi być deterministyczna, taka jak w Block)
        import json
        block_string = json.dumps(signable_data_dict, sort_keys=True)
        data_bytes = block_string.encode('utf-8')
        
        # Podpis
        signature_bytes = self.identity_manager.sign_data(data_bytes)
        signature_hex = signature_bytes.hex()
        
        # Ustawienie podpisu w bloku
        block.extra_data = signature_hex
        
        # Przeliczenie hasha bloku (bo zmieniło się extra_data - chociaż w implementacji Block
        # hash zależy też od extra_data? Sprawdźmy Block.calculate_hash)
        # W Block.calculate_hash: extra_data JEST częścią hasha.
        # Więc musimy przeliczyć hash.
        block.hash = block.calculate_hash()
        
        return block
