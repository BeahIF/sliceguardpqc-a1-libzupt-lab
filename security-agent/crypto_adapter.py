from pathlib import Path
from typing import Any

import zupt


class CryptoAdapter:
    PROFILE_NONE = "NONE"
    PROFILE_LIBZUPT_HYBRID = "LIBZUPT_HYBRID"
    PROFILE_ALIASES = {
        "NONE": PROFILE_NONE,
        "DISABLED": PROFILE_NONE,
        "NO_ENCRYPTION": PROFILE_NONE,
        "CLASSICAL": PROFILE_NONE,

        "LIBZUPT_HYBRID": PROFILE_LIBZUPT_HYBRID,
        "HYBRID_PQC": PROFILE_LIBZUPT_HYBRID,
        "PQC_HYBRID": PROFILE_LIBZUPT_HYBRID,
        "ML_KEM_768_X25519": PROFILE_LIBZUPT_HYBRID,
    }

    def __init__(self, keys_directory: str = "keys") -> None:
        self.keys_directory = Path(keys_directory)
        self.keys_directory.mkdir(parents=True, exist_ok=True)

        self.private_key_path = self.keys_directory / "private.zupt-key"
        self.public_key_path = self.keys_directory / "public.zupt-key"

        self.key_generator = zupt.KeyGenerator()

        self._ensure_keys_exist()

    def _ensure_keys_exist(self) -> None:
        if self.private_key_path.exists() and self.public_key_path.exists():
            return

        print("[crypto] Gerando novo par de chaves híbridas...")

        keypair = self.key_generator.generate_keypair()

        self.key_generator.save_keypair(
            keypair,
            str(self.private_key_path),
        )

        self.key_generator.export_public_key(
            str(self.private_key_path),
            str(self.public_key_path),
        )

        print("[crypto] Chaves geradas com sucesso.")

    def encrypt(
        self,
        payload: bytes,
        profile: str,
    ) -> dict[str, Any]:
        if profile == self.PROFILE_NONE:
            return {
                "profile": profile,
                "ciphertext": payload,
                "header": b"",
                "encrypted": False,
            }

        if profile != self.PROFILE_LIBZUPT_HYBRID:
            raise ValueError(f"Perfil criptográfico não suportado: {profile}")

        public_key = self.key_generator.load_public_key(
            str(self.public_key_path)
        )

        encryptor = zupt.Encryptor(public_key)

        ciphertext, header = encryptor.encrypt(payload)

        return {
            "profile": profile,
            "ciphertext": ciphertext,
            "header": header,
            "encrypted": True,
        }

    def decrypt(
        self,
        ciphertext: bytes,
        header: bytes,
        profile: str,
    ) -> bytes:
        if profile == self.PROFILE_NONE:
            return ciphertext

        if profile != self.PROFILE_LIBZUPT_HYBRID:
            raise ValueError(f"Perfil criptográfico não suportado: {profile}")

        keypair = self.key_generator.load_keypair(
            str(self.private_key_path)
        )

        decryptor = zupt.Decryptor(keypair.secret_key)

        return decryptor.decrypt(ciphertext, list(header))
    
    def normalize_profile(self, profile: str) -> str:
        normalized_value = profile.strip().upper()

        try:
            return self.PROFILE_ALIASES[normalized_value]
        except KeyError as error:
            raise ValueError(
                f"Perfil criptográfico não suportado: {profile}"
            ) from error