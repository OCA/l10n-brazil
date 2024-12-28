# Copyright (C) 2024 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from os import path

from odoo.tools.convert import convert_file


def load_fixture_files(env, module, file_names, idref=None, mode="init"):
    if idref is None:
        idref = {}
    for file_name in file_names:
        if "/" not in file_name:
            file_name = path.join("demo", file_name)
        convert_file(
            env,
            module=module,
            filename=file_name,
            idref=idref,
            mode=mode,
            noupdate=True,
            kind="demo",
        )
