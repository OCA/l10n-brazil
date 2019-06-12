# -*- coding: utf-8 -*-
#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models, api, _
from odoo.exceptions import UserError
from ..constantes import (
    SEQUENCIAL_EMPRESA, SEQUENCIAL_FATURA, SEQUENCIAL_CARTEIRA
)

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def get_invoice_fiscal_number(self):
        """ Como neste modulo nao temos o numero do documento fiscal,
        vamos retornar o numero do core e deixar este metodo
        para caso alguem queira sobrescrever"""

        self.ensure_one()
        return self.number

    @api.multi
    def action_move_create(self):
        result = super(AccountInvoice, self).action_move_create()

        for inv in self:

            # inv.transaction_id = sequence
            for index, interval in enumerate(inv.move_line_receivable_id):
                inv_number = inv.get_invoice_fiscal_number().split('/')[-1]
                numero_documento = (
                    inv_number + '/' + str(index + 1).zfill(2)
                )

                # Verificar se é boleto para criar o numero
                if inv.company_id.own_number_type == SEQUENCIAL_EMPRESA:
                    sequence = inv.company_id.get_own_number_sequence()
                elif inv.company_id.own_number_type == SEQUENCIAL_FATURA:
                    sequence = numero_documento.replace('/', '')
                elif inv.company_id.own_number_type == SEQUENCIAL_CARTEIRA:
                    # TODO: Implementar uma sequencia na carteira de cobranca
                    raise NotImplementedError
                else:
                    raise UserError(_(
                        u"Favor acessar aba Cobrança da configuração da"
                        u" sua empresa para determinar o tipo de "
                        u"sequencia utilizada nas cobrancas"
                    ))

                interval.transaction_ref = sequence
                interval.nosso_numero = sequence if \
                    interval.payment_mode_id.gera_nosso_numero else '0'
                interval.numero_documento = numero_documento
                interval.identificacao_titulo_empresa = hex(
                    interval.id
                ).upper()

        return result

    @api.multi
    def invoice_validate(self):
        result = super(AccountInvoice, self).invoice_validate()
        self.create_account_payment_line()
        return result
