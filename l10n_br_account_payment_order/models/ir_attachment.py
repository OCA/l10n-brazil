# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, models
from odoo.exceptions import ValidationError


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def unlink(self):
        for rec in self:
            if (
                rec.res_model in ["cnab.return.log"]
                and rec.res_id
                and self._uid != SUPERUSER_ID
            ):
                raise ValidationError(
                    _("Sorry, you are not allowed to delete the attachment.")
                )
        return super().unlink()
