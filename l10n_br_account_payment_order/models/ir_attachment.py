# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, _, api, models
from odoo.exceptions import UserError


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.ondelete(at_uninstall=False)
    def _unlink_except_cnab_attachment(self):
        for rec in self:
            if (
                rec.res_model in ["cnab.return.log"]
                and rec.res_id
                and self._uid != SUPERUSER_ID
            ):
                raise UserError(
                    _("Sorry, you are not allowed to delete the attachment.")
                )
