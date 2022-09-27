from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    cnab_structure_id = fields.Many2one(
        comodel_name="l10n_br_cnab.structure",
        related="payment_mode_id.cnab_structure_id",
    )

    def get_file_name(self, cnab_type):
        context_today = fields.Date.context_today(self)
        if cnab_type == "240":
            return "CB%s%s.REM" % (
                context_today.strftime("%d%m"),
                str(self.file_number),
            )
        elif cnab_type == "400":
            return "CB%s%02d.REM" % (
                context_today.strftime("%d%m"),
                self.file_number or 1,
            )
        elif cnab_type == "500":
            return "PG%s%s.REM" % (
                context_today.strftime("%d%m"),
                str(self.file_number),
            )

    def generate_payment_file(self):
        """Returns (payment file as string, filename)"""
        self.ensure_one()

        cnab_type = self.payment_mode_id.payment_method_code

        # Se não for um caso CNAB deve chamar o super
        if (
            cnab_type not in ("240", "400", "500")
            or self.payment_mode_id.cnab_processor != "oca_processor"
        ):
            return super().generate_payment_file()

        str_file = self.cnab_structure_id.output(self).encode("utf-8")
        return str_file, self.get_file_name(cnab_type)

    def generated2uploaded(self):
        super().generated2uploaded()
        for payment_line in self.payment_line_ids:
            # No caso de Cancelamento da Invoice a AML é apagada
            if payment_line.move_line_id:
                # Importante para saber a situação do CNAB no caso
                # de um pagto feito por fora ( dinheiro, deposito, etc)
                payment_line.move_line_id.cnab_state = "exported"
