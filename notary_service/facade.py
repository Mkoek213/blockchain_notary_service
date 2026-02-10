import os
from typing import TYPE_CHECKING, List, Optional, cast

from blockchain_core.block_builder import Block, BlockBuilder
from blockchain_core.crypto_service import ICryptoService
from blockchain_core.interfaces import IBlockchainInterface
from blockchain_core.notarial_document import NotarialDocument
from business_logic.business_logic_module import BusinessLogicModule
from business_logic.notary_validator import NotaryValidator
from business_logic.world_state import SimpleWorldState
from network.network_manager import NetworkManager

if TYPE_CHECKING:
    from security.identity_manager import IdentityManager

from notary_service.document_registry import DocumentRegistry
from notary_service.persistent_blockchain import PersistentBlockchain
from notary_service.storage import JsonStorageProvider, JsonWorldStateManager


class NotaryService:
    """Fasada łącząca istniejące moduły bez ich modyfikacji."""

    def __init__(
        self,
        *,
        use_storage: bool = False,
        data_dir: str = "data",
        enable_network: bool = False,
        identity_manager: Optional["IdentityManager"] = None,
        crypto_service: Optional[ICryptoService] = None,
    ) -> None:
        self.document_registry = DocumentRegistry()

        storage_provider = None
        world_state_manager: SimpleWorldState
        ledger_repo = None
        if use_storage:
            ledger_path = os.path.join(data_dir, "ledger.json")
            state_path = os.path.join(data_dir, "world_state.json")
            storage_provider = JsonStorageProvider(ledger_path)
            ledger_repo = storage_provider.ledger
            world_state_manager = JsonWorldStateManager(state_path, ledger_repo)
            world_state_manager.load()
        else:
            world_state_manager = SimpleWorldState()

        self.world_state = world_state_manager
        self.notary_validator = NotaryValidator(crypto_service=crypto_service)
        self.business_logic = BusinessLogicModule(world_state_manager)
        self.blockchain = PersistentBlockchain(
            storage_provider=storage_provider,
            notary_validator=self.notary_validator,
            crypto_service=crypto_service,
            world_state_manager=world_state_manager,
        )

        self.network_manager: Optional[NetworkManager] = None
        if enable_network:
            self.network_manager = NetworkManager(
                chain=cast(IBlockchainInterface, self.blockchain),
                identity_manager=identity_manager,
            )

    def create_document(self, data: dict) -> NotarialDocument:
        return self.document_registry.create_document(data)

    def validate_document(self, data: dict) -> bool:
        structural_ok = True
        if self.notary_validator is not None:
            structural_ok = self.notary_validator.validate_document(data)
        business_ok = self.business_logic.validate_transaction(data, self.world_state)
        return structural_ok and business_ok

    def build_block(
        self,
        author: str,
        documents: List[NotarialDocument],
        sign: bool = False,
        private_key: Optional[str] = None,
    ) -> Block:
        parent_hash = self.blockchain.get_last_block().get_hash()
        builder = BlockBuilder()
        builder.set_parent_hash(parent_hash)
        builder.set_author(author)
        for doc in documents:
            builder.add_document(doc)
        if sign:
            if private_key is None or self.blockchain.crypto_service is None:
                raise ValueError("Signing requested but crypto_service or private_key missing")
            return builder.build(self.blockchain.crypto_service, private_key)
        return builder.build()

    def add_block(self, block: Block) -> bool:
        return self.blockchain.append_block(block)

    def start_network(self, port: int = 8545) -> None:
        if self.network_manager is None:
            return
        self.network_manager.start(port)

    def stop_network(self) -> None:
        if self.network_manager is None:
            return
        self.network_manager.stop()

    def broadcast_block(self, block: Block) -> None:
        if self.network_manager is None:
            return
        self.network_manager.broadcast_block(block)
