"""Connexion SSH par mot de passe (Paramiko) et exécution de commandes.

Auth par mot de passe uniquement (lab, pas de clé). Les commandes privilégiées
passent par `sudo -S` en injectant le mot de passe SSH sur stdin.
"""
import socket

import paramiko
from loguru import logger


class SSHError(Exception):
    """Échec de connexion ou d'exécution SSH."""


class SSHSession:
    """Session SSH ouverte sur une VM. À utiliser comme context manager."""

    def __init__(self, host: str, user: str, password: str, timeout: int = 10) -> None:
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self._client: paramiko.SSHClient | None = None

    def __enter__(self) -> "SSHSession":
        self.connect()
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def connect(self) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.host,
                username=self.user,
                password=self.password,
                timeout=self.timeout,
                allow_agent=False,
                look_for_keys=False,
            )
        except (paramiko.AuthenticationException,) as exc:
            raise SSHError("mauvais user/mot de passe") from exc
        except (paramiko.SSHException, socket.error, OSError) as exc:
            raise SSHError(f"IP injoignable ({exc})") from exc
        self._client = client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def run(self, command: str, sudo: bool = False) -> tuple[int, str, str]:
        """Exécute une commande, renvoie (code retour, stdout, stderr).

        Privilèges : si l'utilisateur est déjà root, exécution directe (pas de
        sudo, qui peut être absent d'une Debian minimale). Sinon `sudo -S` avec
        le mot de passe injecté sur stdin."""
        if self._client is None:
            raise SSHError("session non connectée")
        is_root = self.user == "root"
        need_password = sudo and not is_root
        if sudo:
            prefix = "" if is_root else "sudo -S -p '' "
            command = f"{prefix}bash -c {_shell_quote(command)}"
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=60)
            if need_password:
                stdin.write(self.password + "\n")
                stdin.flush()
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            code = stdout.channel.recv_exit_status()
            return code, out, err
        except (paramiko.SSHException, socket.error, OSError) as exc:
            logger.error(f"Commande échouée sur {self.host}: {exc}")
            raise SSHError(str(exc)) from exc


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def test_connection(host: str, user: str, password: str) -> tuple[bool, str]:
    """Teste une connexion SSH sans rien exécuter. Renvoie (ok, message)."""
    try:
        with SSHSession(host, user, password):
            return True, "Connexion réussie"
    except SSHError as exc:
        return False, f"Échec : {exc} — mauvais user/mot de passe ou IP injoignable"
