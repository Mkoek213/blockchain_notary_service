from typing import Optional

from blockchain_core.blockchain import Blockchain
from blockchain_core.crypto_service import ICryptoService
from blockchain_core.interfaces import INotaryValidator, IStorageProvider
from notary_service.block_codec import block_from_dict


class PersistentBlockchain(Blockchain):
    """Blockchain z integracją Storage oraz World State bez modyfikacji core."""

    def __init__(
        self,
        storage_provider: Optional[IStorageProvider] = None,
        notary_validator: Optional[INotaryValidator] = None,
        crypto_service: Optional[ICryptoService] = None,
        world_state_manager: Optional[object] = None,
    ) -> None:
        self.world_state_manager = world_state_manager
        super().__init__(
            storage_provider=storage_provider,
            notary_validator=notary_validator,
            crypto_service=crypto_service,
        )

    def _initialize_chain(self) -> None:
        loaded_blocks = []
        if self.storage_provider:
            loaded_chain = self.storage_provider.load_blockchain()
            if loaded_chain:
                for block_data in loaded_chain:
                    block = block_from_dict(block_data)
                    if block is None:
                        continue
                    loaded_blocks.append(block)
        if loaded_blocks:
            self.chain = loaded_blocks
        else:
            self._create_genesis_block()

        if self.world_state_manager is not None:
            loaded_state = False
            if hasattr(self.world_state_manager, "load"):
                try:
                    loaded_state = self.world_state_manager.load()
                except Exception:
                    loaded_state = False
            if not loaded_state and hasattr(self.world_state_manager, "build_from_blockchain"):
                self.world_state_manager.build_from_blockchain(self)

    def append_block(self, block) -> bool:
        success = super().append_block(block)
        if success and self.world_state_manager is not None:
            try:
                if hasattr(self.world_state_manager, "update_state"):
                    self.world_state_manager.update_state(block)
                elif hasattr(self.world_state_manager, "_process_block"):
                    # SimpleWorldState doesn't implement update_state; apply block directly.
                    self.world_state_manager._process_block(block)
                if hasattr(self.world_state_manager, "save"):
                    self.world_state_manager.save()
            except Exception:
                pass
        return success
