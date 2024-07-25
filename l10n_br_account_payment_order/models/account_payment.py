# © 2012 KMEE INFORMATICA LTDA
#   @author  Daniel Sadamo Hirayama <daniel.sadamo@kmee.com.br>
#   @author  Hugo Uchôas Borges <hugo.borges@kmee.com.br>
# Copyright (C) 2021-Today - Akretion (<http://www.akretion.com>).
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from ..constants import BR_CODES_PAYMENT_ORDER


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        for record in self:
            if (
                record.payment_method_code in BR_CODES_PAYMENT_ORDER
                and record.payment_method_id.payment_type == "inbound"
            ):
                # TODO - Idealmente isso deveria ser resolvido com um
                #  domain=[('code', 'not in', BR_CODES_PAYMENT_ORDER)]
                #  no campo payment_method_id, mas mesmo adicionando isso na
                #  visão ou sobre escrevendo o campo não funciona e não gera
                #  erros, não consegui identificar o motivo do problema (
                #  seria algum problema no orm ? Não encontrei um issue aberto
                #  com referencia a isso ), para reproduzir o erro basta tentar
                #  incluir o domain no campo como comentado acima e testar
                #  na tela.
                #  Testar na migração.
                raise UserError(
                    _(
                        "CNAB Payment Method can't be used to make"
                        " direct Payments, just used in Payment Orders,"
                        " choose another one."
                    )
                )

        return super().action_post()
