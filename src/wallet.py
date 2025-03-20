import codecs
import hashlib
import base58

from ecdsa import NIST256p, SigningKey

from Crypto.Hash import RIPEMD160

from src.utils import dict_utils


class Wallet:
    def __init__(self):
        self._private_key = SigningKey.generate(curve=NIST256p)
        self._public_key = self._private_key.get_verifying_key()
        self._blockchain_address = self.generate_blockchain_address()

    @property
    def blockchain_address(self) -> str:
        return self._blockchain_address

    @property
    def private_key(self) -> str:
        return self._private_key.to_string().hex()

    @property
    def public_key(self) -> str:
        return self._public_key.to_string().hex()

    def generate_blockchain_address(self) -> str:
        public_key_bytes = self._public_key.to_string()
        sha256_bpk = hashlib.sha256(public_key_bytes)
        sha256_bpk_digest = sha256_bpk.digest()

        ripemd160_bpk = RIPEMD160.new()
        ripemd160_bpk.update(sha256_bpk_digest)
        ripemd160_bpk_digest = ripemd160_bpk.digest()
        ripemd160_bpk_digest_hex = codecs.encode(ripemd160_bpk_digest, "hex")

        network_coin_public_key = b"00" + ripemd160_bpk_digest_hex
        network_coin_public_key_bytes = codecs.decode(network_coin_public_key, "hex")

        sha256_bpk_digest = hashlib.sha256(network_coin_public_key_bytes).digest()
        sha256_2_bpk_digest = hashlib.sha256(sha256_bpk_digest).digest()
        sha256_hex = codecs.encode(sha256_2_bpk_digest, "hex")

        checksum = sha256_hex[:8]

        addr_hex = (network_coin_public_key + checksum).decode("utf-8")

        blockchain_addr = base58.b58encode(addr_hex).decode("utf-8")

        return blockchain_addr

    @staticmethod
    def generate_signature(
        send_blockchain_addr: str,
        recv_blockchain_addr: str,
        send_private_key: str,
        amount: float,
    ) -> str:
        transaction = dict_utils.sorted_dict_by_key(
            {
                "send_blockchain_addr": send_blockchain_addr,
                "recv_blockchain_addr": recv_blockchain_addr,
                "amount": float(amount),
            }
        )
        sha256 = hashlib.sha256()
        sha256.update(str(transaction).encode("utf-8"))

        message = sha256.digest()

        private_key = SigningKey.from_string(
            bytes().fromhex(send_private_key),
            curve=NIST256p,
        )
        private_key_sign = private_key.sign(message)

        signature = private_key_sign.hex()

        return signature
