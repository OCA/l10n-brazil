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
        string="Name",
        index=True,
        track_visibility="always",
    )
    code = fields.Char(
        string="Code",
        index=True,
        track_visibility="always",
    )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s - %s" % (record.code, record.name)))
        return result

    @api.constrains("code")
    def check_code(self):
        for record in self:
            # Tamanho do campo é padrão 2 p/ todos os codigos CNAB ?
            if len(record.code) != 2:
                raise ValidationError(_("The field Code should have two characters."))

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
                    _("The Code %s already exist %s for Bank and CNAB type.")
                    % (record.code, code_name_exist)
                )
