# Copyright (C) 2023 - TODAY Raphaël Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from .hooks import pre_init_hook
from .hooks import post_init_hook

from . import models
from . import wizards
from . import report

from odoo.api import Environment
from odoo.models import NewId


def add_to_compute(self, field, records):
    """
    Mark ``field`` to be computed on ``records``.
    Monkey patched to avoid recomputing account.move
    and account.move.line linked to the same dummy records
    used in non fiscal account moves.
    """
    if records and self.context.get(
        "recompute_%s_after_id" % (records._name.replace(".", "_"),)
    ):
        records = records.filtered(
            lambda rec: isinstance(rec.id, NewId)
            or rec.id
            > self.context["recompute_%s_after_id" % (records._name.replace(".", "_"),)]
        )

    return Environment.add_to_compute._original_method(self, field, records)


add_to_compute._original_method = Environment.add_to_compute
Environment.add_to_compute = add_to_compute
