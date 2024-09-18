# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nBrCNABDataAbstract(models.AbstractModel):
    _name = "l10n_br_cnab.data.abstract"
    _inherit = "mail.thread"
    _description = "CNAB Data Abstract"

    name = fields.Char(
        index=True,
        tracking=True,
    )
    code = fields.Char(
        index=True,
        tracking=True,
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.code} - {record.name}"))
        return result

    @api.constrains("code")
    def check_code(self):
        for record in self:
            # Mesmo o record que está sendo alterado não ter sido ainda salvo
            # a pesquisa acaba trazendo ele, por isso o filtro 'id'
            code_already_exist = record.search(
                [
                    ("id", "!=", record.id),
                    ("code", "=", record.code),
                    ("payment_method_ids", "in", record.payment_method_ids.ids),
                    ("bank_ids", "in", record.bank_ids.ids),
                ]
            )
            if code_already_exist:
                code_name_exist = (
                    code_already_exist.code + " - " + code_already_exist.name
                )
                raise ValidationError(
                    _(
                        "The Code %(code)s already exist %(code_name_exist)s for Bank "
                        "and CNAB type.",
                        code=record.code,
                        code_name_exist=code_name_exist,
                    )
                )
