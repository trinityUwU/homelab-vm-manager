"""Isolation de l'accès aux secrets (mots de passe SSH).

Seule concession future-proof demandée : tout passage par les mots de passe
transite par ce module. Aujourd'hui ils sont stockés en clair dans le JSON
(lab isolé). Pour ajouter du chiffrement plus tard, il suffit de modifier
`seal` / `reveal` ici — aucun autre fichier ne touche aux secrets en clair.
"""


def seal(plaintext: str) -> str:
    """Transforme un secret avant stockage. Aujourd'hui : identité."""
    return plaintext or ""


def reveal(stored: str) -> str:
    """Restaure un secret lu depuis le stockage. Aujourd'hui : identité."""
    return stored or ""
