# Copyright 2024-TODAY - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nBrCNABCode(models.Model):
    _name = "l10n_br_cnab.code"
    _inherit = "mail.thread"
    _description = "CNAB Code"

    name = fields.Char(
        index=True,
        tracking=True,
        required=True,
    )

    code = fields.Char(
        index=True,
        tracking=True,
        required=True,
    )

    code_type = fields.Selection(
        index=True,
        tracking=True,
        required=True,
        selection=[
            ("instruction_move_code", "Instruction Move Code"),
            ("return_move_code", "Return Move Code"),
            ("wallet_code", "Wallet Code"),
            ("discount_code", "Discount Code"),
            ("protest_code", "Protest Code"),
            ("fee_code", "Fee Code"),
            ("interest_code", "Interest Code"),
            ("boleto_species", "Boleto Species"),
            ("boleto_accept", "Boleto Accept"),
            ("doc_finality_code", "DOC Finality Code"),
            ("ted_finality_code", "TED Finality Code"),
            ("complementary_finality_code", "Complementary Finality Code"),
            ("service_type", "Service Type"),
            ("release_form", "Release Form"),
            ("boleto_wallet", "Boleto Wallet"),
            ("boleto_modality", "Boleto Modality"),
            ("boleto_variation", "Boleto Variation"),
            ("boleto_write_off_devolution", "Boleto Write Off Devolution"),
        ],
    )

    bank_ids = fields.Many2many(
        string="Banks",
        comodel_name="res.bank",
        relation="l10n_br_cnab_code_bank_rel",
        column1="bank_id",
        column2="l10n_br_cnab_code_id",
        tracking=True,
        required=True,
    )

    payment_method_ids = fields.Many2many(
        comodel_name="account.payment.method",
        string="Payment Methods",
        relation="l10n_br_cnab_code_payment_method_rel",
        column1="payment_method_id",
        column2="l10n_br_cnab_code_id",
        tracking=True,
        required=True,
    )

    comment = fields.Text()

    # TODO: Deve ser considerado em apagar o campo many2many e deixar
    #  apenas o many2one já que, por enquanto, não há bancos diferentes
    #  usando o mesmo conjunto de codigos apenas diferentes cnab( 240/400
    #  são iguais no caso Unicred )
    # bank_id = fields.Many2one(comodel_name="res.bank")

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
                    ("code_type", "=", record.code_type),
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
                        "The Code %(code)s %(name)s already exists for Bank %(bank)s "
                        "and CNAB %(type_code)s type.",
                        code=record.code,
                        name=code_name_exist,
                        bank=code_already_exist.bank_ids.mapped("name"),
                        type_code=code_already_exist.payment_method_ids.mapped("code"),
                    )
                )

            # Tamanho do campo é padrão 2 p/ todos
            # os codigos de Instrução CNAB ?
            if len(record.code) != 2 and record.code_type in (
                "instruction_move_code",
                "return_move_code",
            ):
                raise ValidationError(
                    _(
                        "The field Code in 'Instruction and Return Move Code'"
                        " should have two characters."
                    )
                )
