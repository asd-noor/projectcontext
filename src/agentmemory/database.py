# Agent Memory - MCP Server for long-term memory storage
# Copyright (C) 2026  Asaduzzaman Noor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Database configuration and utilities."""

import os
import subprocess

# --- CONFIG ---
DB_DIR = ".ctxhub"

DB_NAMES = {
    "memory": "memory.sqlite",
    "agenda": "agenda.sqlite",
}

# def get_db_path() -> str:
#     """Determine the database path (git root or current directory)."""
#     dbdir = DB_DIR
#     dbfile = DB_FILE
#     try:
#         # Use git to find the root directory
#         git_root = (
#             subprocess.check_output(
#                 ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
#             )
#             .decode("utf-8")
#             .strip()
#         )
#         return os.path.join(git_root, dbdir, dbfile)
#     except (subprocess.CalledProcessError, FileNotFoundError):
#         # Fallback to current working directory if not a git repo or git not found
#         return os.path.join(os.getcwd(), dbdir, dbfile)


def determine_db_dir() -> str:
    """Determine the database directory (git root or current directory)."""
    try:
        # Use git to find the root directory
        git_root = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL
            )
            .decode("utf-8")
            .strip()
        )

        db_path = os.path.join(git_root, DB_DIR)
        os.makedirs(db_path, exist_ok=True)
        return os.path.join(git_root, DB_DIR)

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to current working directory if not a git repo or git not found
        db_path = os.path.join(os.getcwd(), DB_DIR)
        os.makedirs(db_path, exist_ok=True)
        return db_path


def get_memory_db_path() -> str:
    """Determine the database path."""
    dbdir = determine_db_dir()
    return os.path.join(dbdir, DB_NAMES["memory"])


def get_agenda_db_path() -> str:
    """Determine the agenda database path."""
    dbdir = determine_db_dir()
    return os.path.join(dbdir, DB_NAMES["agenda"])


# DB_PATH = get_db_path()
