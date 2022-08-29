# Copyright (C) 2022-Today - Engenere (<https://engenere.one>).
# @author Antônio S. Pereira Neto <neto@engenere.one>
# @author Felipe Motter Pereira <felipe@engenere.one>
# Copyright (C) 2022-Today - Akretion (<https://akretion.com/pt-BR>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.l10n_br_fiscal.constants.fiscal import FISCAL_PAYMENT_MODE


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    fiscal_payment_mode = fields.Selection(
        selection=FISCAL_PAYMENT_MODE,
        string="Meio de Pagamento da NF",
        help="Obrigatório o preenchimento do Grupo Informações de Pagamento"
        " para NF-e e NFC-e. Para as notas com finalidade de Ajuste"
        " ou Devolução o campo Forma de Pagamento deve ser preenchido"
        " com 90 - Sem Pagamento.",
    )
