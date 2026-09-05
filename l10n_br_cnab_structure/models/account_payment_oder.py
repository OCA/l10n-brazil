# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    cnab_processor = fields.Selection(
        selection="_selection_cnab_processor", compute="_compute_cnab_processor"
    )

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure", compute="_compute_cnab_structure_id"
    )

    @api.model
    def _selection_cnab_processor(self):
        return self.env["account.payment.mode"]._selection_cnab_processor()

    def _compute_cnab_processor(self):
        for order in self:
            order.cnab_processor = order.payment_mode_id.cnab_processor
            if order.cnab_processor:
                return
            if order.payment_type == "outbound":
                order.cnab_processor = order.journal_id.default_outbound_cnab_processor

    def _compute_cnab_structure_id(self):
        for order in self:
            order.cnab_structure_id = order.payment_mode_id.cnab_structure_id
            if order.cnab_structure_id:
                return
            if order.payment_type == "outbound":
                order.cnab_structure_id = (
                    order.journal_id.default_outbound_cnab_structure_id
                )

    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()

        cnab_type = self.payment_mode_id.payment_method_code

        # Se não for um caso CNAB deve chamar o super
        if (
            cnab_type not in ("240", "400", "500")
            or self.cnab_processor != "oca_processor"
        ):
            return super().generate_payment_file()

        str_file = self.cnab_structure_id.output(self).encode("utf-8")
        return str_file, self.get_file_name(cnab_type)

    def generated2uploaded(self):
        result = super().generated2uploaded()
        for payment_line in self.payment_line_ids:
            # No caso de Cancelamento da Invoice a AML é apagada
            if payment_line.move_line_id:
                # Importante para saber a situação do CNAB no caso
                # de um pagto feito por fora ( dinheiro, deposito, etc)
                payment_line.move_line_id.cnab_state = "exported"
        return result
