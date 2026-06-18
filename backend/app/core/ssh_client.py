"""Connexion SSH par mot de passe (Paramiko) et exécution de commandes.

Auth par mot de passe uniquement (lab, pas de clé). Les commandes privilégiées
passent par `sudo -S` en injectant le mot de passe SSH sur stdin.
"""
import socket
from collections.abc import Callable

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

    def run(self, command: str, sudo: bool = False, timeout: int = 60) -> tuple[int, str, str]:
        """Exécute une commande, renvoie (code retour, stdout, stderr).

        Privilèges : si l'utilisateur est déjà root, exécution directe (pas de
        sudo, qui peut être absent d'une Debian minimale). Sinon `sudo -S` avec
        le mot de passe injecté sur stdin. `timeout` plafonne la durée d'exécution."""
        if self._client is None:
            raise SSHError("session non connectée")
        is_root = self.user == "root"
        need_password = sudo and not is_root
        if sudo:
            prefix = "" if is_root else "sudo -S -p '' "
            command = f"{prefix}bash -c {_shell_quote(command)}"
        try:
            stdin, stdout, stderr = self._client.exec_command(command, timeout=timeout)
            if need_password:
                stdin.write(self.password + "\n")
                stdin.flush()
            out = stdout.read().decode("utf-8", "replace")
            err = stderr.read().decode("utf-8", "replace")
            code = stdout.channel.recv_exit_status()
            return code, out, err
        except (socket.timeout, TimeoutError) as exc:
            logger.error(f"Commande expirée sur {self.host} (>{timeout}s): {command[:80]}")
            raise SSHError(f"délai d'exécution dépassé (>{timeout}s)") from exc
        except (paramiko.SSHException, socket.error, OSError) as exc:
            logger.error(f"Commande échouée sur {self.host}: {exc!r}")
            raise SSHError(str(exc) or type(exc).__name__) from exc


    def exec_stream(
        self,
        command: str,
        on_line: Callable[[str], None],
        sudo: bool = False,
        timeout: int = 900,
    ) -> int:
        """Exécute une commande en diffusant sa sortie ligne par ligne (live).

        Pas de PTY : apt désactive alors ses barres de progression et sort des
        lignes propres. stderr est fusionné dans stdout pour l'ordre réel. Renvoie
        le code de sortie. Filtre l'écho éventuel du mot de passe sudo.
        """
        if self._client is None:
            raise SSHError("session non connectée")
        is_root = self.user == "root"
        need_password = sudo and not is_root
        if sudo:
            prefix = "" if is_root else "sudo -S -p '' "
            command = f"{prefix}bash -c {_shell_quote(command)}"
        try:
            chan = self._client.get_transport().open_session(timeout=self.timeout)
            chan.set_combine_stderr(True)
            chan.settimeout(timeout)
            chan.exec_command(command)
            if need_password:
                chan.sendall(self.password + "\n")
            return self._drain(chan, on_line)
        except (socket.timeout, TimeoutError) as exc:
            raise SSHError(f"délai d'exécution dépassé (>{timeout}s)") from exc
        except (paramiko.SSHException, socket.error, OSError) as exc:
            logger.error(f"Stream échoué sur {self.host}: {exc!r}")
            raise SSHError(str(exc) or type(exc).__name__) from exc

    def _drain(self, chan: "paramiko.Channel", on_line: Callable[[str], None]) -> int:
        """Lit le canal jusqu'à EOF, émet chaque ligne complète, masque le mot de passe."""
        buf = ""
        while True:
            data = chan.recv(4096)
            if not data:
                break
            buf += data.decode("utf-8", "replace")
            *lines, buf = buf.split("\n")
            for line in lines:
                self._emit_line(line, on_line)
        self._emit_line(buf, on_line)
        return chan.recv_exit_status()

    def _emit_line(self, line: str, on_line: Callable[[str], None]) -> None:
        """Nettoie un résidu éventuel de `\\r` et filtre lignes vides / mot de passe."""
        clean = line.replace("\r", "").rstrip()
        if clean and not (self.password and self.password in clean):
            on_line(clean)


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def test_connection(host: str, user: str, password: str) -> tuple[bool, str]:
    """Teste une connexion SSH sans rien exécuter. Renvoie (ok, message)."""
    try:
        with SSHSession(host, user, password):
            return True, "Connexion réussie"
    except SSHError as exc:
        return False, f"Échec : {exc} — mauvais user/mot de passe ou IP injoignable"
