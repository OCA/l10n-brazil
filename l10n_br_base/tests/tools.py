"""Helpers for loading demo data as test fixtures."""

from odoo.tools.convert import convert_file


def load_fixture_files(env, module, file_names):
    """Load XML fixture files from a module's demo directory."""
    for file_name in file_names:
        convert_file(env, module, file_name, {}, "init", noupdate=True)
