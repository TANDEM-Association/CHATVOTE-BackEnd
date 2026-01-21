#!/usr/bin/env python3
"""Helper script to generate a SHA1 password hash for securing Jupyter Lab."""

from __future__ import annotations

import argparse
import binascii
import hashlib
import os
import sys
from getpass import getpass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a password hash compatible with Jupyter Server."
    )
    parser.add_argument(
        "password",
        nargs="?",
        help="Plain-text password to hash. If omitted, you will be prompted securely.",
    )
    parser.add_argument(
        "--salt-length",
        type=int,
        default=12,
        help="Number of random bytes to use for the salt (default: %(default)s).",
    )
    return parser.parse_args()


def read_password_from_prompt() -> str:
    first = getpass("Enter Jupyter password: ")
    confirm = getpass("Confirm password: ")
    if first != confirm:
        print("Passwords do not match. Aborting.", file=sys.stderr)
        raise SystemExit(1)
    if not first:
        print("Password cannot be empty. Aborting.", file=sys.stderr)
        raise SystemExit(1)
    return first


def hash_password(password: str, salt_length: int) -> str:
    salt_bytes = os.urandom(salt_length)
    salt = binascii.hexlify(salt_bytes).decode("ascii")
    digest = hashlib.sha1()
    digest.update(password.encode("utf-8"))
    digest.update(salt.encode("ascii"))
    return f"sha1:{salt}:{digest.hexdigest()}"


def main() -> None:
    args = parse_args()
    password = args.password or read_password_from_prompt()
    hashed = hash_password(password, args.salt_length)
    print(hashed)


if __name__ == "__main__":
    main()
