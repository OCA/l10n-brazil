# © 2019 KMEE INFORMATICA LTDA
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    _name = "account.move"
    # TODO: remover herança mail.thread aqui na v14, por já ser feita pelo core
    _inherit = [_name, "mail.thread"]

    cnab_return_log_id = fields.Many2one(
        string="CNAB Return Log",
        comodel_name="l10n_br_cnab.return.log",
        readonly=True,
        inverse_name="move_id",
    )

    # Usados para deixar invisivel o campo
    # relacionado ao CNAB na visao
    is_cnab = fields.Boolean(string="Is CNAB?")

    def unlink(self):

        # Verificar se é necessário solicitar a Baixa no caso de CNAB
        cnab_already_start = False
        for l_aml in self.mapped("line_ids"):
            if l_aml._cnab_already_start():
                # Se exitir um caso já deve ser feito
                cnab_already_start = l_aml._cnab_already_start()
                break

        if cnab_already_start:
            # Solicitar a Baixa do CNAB
            invoice = self.env["account.invoice"].search([("move_id", "=", self.id)])
            for l_aml in invoice.mapped("financial_move_line_ids"):
                l_aml.update_cnab_for_cancel_invoice()

        return super().unlink()
