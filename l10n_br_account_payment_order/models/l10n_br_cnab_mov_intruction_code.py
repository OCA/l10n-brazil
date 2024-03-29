# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nBrCNABMovInstructionCode(models.Model):
    _name = "l10n_br_cnab.mov.instruction.code"
    _inherit = ["l10n_br_cnab.data.abstract", "mail.thread"]
    _description = "CNAB Movement Instruction Code"

    bank_ids = fields.Many2many(
        string="Banks",
        comodel_name="res.bank",
        relation="l10n_br_cnab_mov_instruction_code_bank_rel",
        column1="bank_id",
        column2="l10n_br_cnab_mov_instruction_code_id",
        tracking=True,
    )

    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method",
        string="Payment Methods",
        relation="l10n_br_cnab_mov_instruction_code_payment_method_rel",
        column1="payment_method_id",
        column2="l10n_br_cnab_mov_instruction_code_id",
        tracking=True,
    )

    comment = fields.Text()

    # TODO: Forma encontrada para pode fazer o Group By, na v15
    #  parece já ser possivel usar campos many2many.
    #  Também deve ser considerado em apagar o campo many2many e deixar
    #  apenas o many2one já que, por enquanto, não há bancos diferentes
    #  usando o mesmo conjunto de codigos apenas diferentes cnab( 240/400
    #  são iguais no caso Unicred )
    bank_id = fields.Many2one(
        comodel_name="res.bank", compute="_compute_bank_id", store=True
    )  # it is possible to search only among stored fields

    payment_method_id = fields.Many2one(
        comodel_name="account.payment.method",
        compute="_compute_payment_method_id",
        store=True,
    )  # it is possible to search only among stored fields

    @api.depends("bank_ids")
    def _compute_bank_id(self):
        for record in self:
            record.bank_id = record.bank_ids and record.bank_ids[0] or False

    @api.depends("payment_method_ids")
    def _compute_payment_method_id(self):
        for record in self:
            record.payment_method_id = (
                record.payment_method_ids and record.payment_method_ids[0] or False
            )

    @api.constrains("code")
    def check_code(self):
        for record in self:
            # Tamanho do campo é padrão 2 p/ todos
            # os codigos de Instrução CNAB ?
            if len(record.code) != 2:
                raise ValidationError(_("The field Code should have two characters."))
            return super().check_code()
