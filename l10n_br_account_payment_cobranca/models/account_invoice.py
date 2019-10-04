# -*- coding: utf-8 -*-
#    @author Danimar Ribeiro <danimaribeiro@gmail.com>
# © 2012 KMEE INFORMATICA LTDA
#   @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from pyboleto.bank_api.itau import ApiItau

from odoo.addons.queue_job.job import job
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from ..constantes import (
    SEQUENCIAL_EMPRESA, SEQUENCIAL_FATURA, SEQUENCIAL_CARTEIRA
)

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    eval_state_cnab = fields.Selection(
        string=u'Estado CNAB',
        related='move_line_receivable_id.state_cnab',
        readonly=True,
        store=True,
    )

    eval_situacao_pagamento = fields.Selection(
        string=u'Situação do Pagamento',
        related='move_line_receivable_id.situacao_pagamento',
        readonly=True,
        store=True,
    )

    eval_payment_mode_instrucoes = fields.Text(
        string=u'Instruções de Cobrança do Modo de Pagamento',
        related='payment_mode_id.instrucoes',
        readonly=True,
    )

    instrucoes = fields.Text(
        string=u'Instruções de cobrança',
    )

    bank_api_operation_ids = fields.One2many(
        string='Operações Realizadas',
        comodel_name='bank.api.operation',
        inverse_name='invoice_id',
        readonly=True,
    )

    @api.multi
    def action_invoice_cancel(self):
        for record in self:
            if record.eval_state_cnab == 'accepted':
                raise UserError(_(
                    "A fatura não pode ser cancelada pois já foi aprovada "
                    "no Banco."
                ))
            if record.eval_state_cnab == 'done':
                raise UserError(_(
                    "Não é possível cancelar uma fatura finalizada."
                ))
            if record.eval_state_cnab == 'exported':
                raise UserError(_(
                    "A fatura não pode ser cancelada pois já foi exportada "
                    "em uma remessa."
                ))

            payment_order_ids = self.env['account.payment.order'].search([
                ('payment_line_ids.move_line_id', 'in',
                 [record.move_line_receivable_id.id])
            ])

            if payment_order_ids:
                if any(state in ['draft', 'cancel'] for state in
                       payment_order_ids.mapped('state')):
                    raise UserError(_(
                        "Para cancelar a fatura, você deve retirá-la das "
                        "ordens de pagamento em aberto em que a mesma "
                        "se encontra. Ordem de Débito %s"
                    ) % '.'.join(payment_order_ids.mapped('name')))
                raise UserError(_(
                    "A fatura não pode ser cancelada pois a mesma já se "
                    "encontra exportada por uma ordem de pagamento."
                ))

        super(AccountInvoice, self).action_invoice_cancel()

    def create_bank_api_operation(self, request, operation_type=False,
                                  environment=False):
        # 'not request' não é válido para o propósito
        if request == False:
            return

        operation_model = self.env['bank.api.operation']

        if not operation_type:
            operation_type = 'post'

        data = {
            'operation_type': operation_type,
            'invoice_id': self.id,
            'environment': environment,
        }

        operation_id = operation_model.create(data)
        operation_id.register_post(request)
        self.bank_api_operation_ids += operation_id

    @job
    @api.multi
    def register_invoice_api(self):
        for record in self:
            receivable_ids = record.mapped('move_line_receivable_id')
            if not receivable_ids:
                return False

            boleto_list = receivable_ids.generate_boleto(validate=False)
            if not boleto_list:
                raise UserError(_(
                    u"Não foi possível registrar as faturas pela API"
                ))

            company_id = record.partner_id.company_id.sudo()

            client_id = company_id.client_id
            client_secret = company_id.client_secret
            itau_key = company_id.itau_key
            endpoint = company_id.api_endpoint
            barcode_endpoint = company_id.raiz_endpoint
            environment = company_id.environment

            token = company_id.api_itau_token
            if not token or company_id.api_itau_token_due_datetime <= \
                    fields.Datetime.now():
                token_request = False
                try:
                    token_request = ApiItau.generate_api_key(
                        client_id, client_secret, endpoint)
                    token_request_dict = json.loads(token_request.content)
                    token = token_request_dict.get('access_token')
                    company_id.api_itau_token = token
                    company_id.api_itau_token_due_datetime = \
                        fields.Datetime.context_timestamp(
                            record, datetime.now()) + relativedelta(
                            seconds=token_request_dict.get('expires_in'))

                except Exception as e:
                    company_id.api_itau_token = ''
                    company_id.api_itau_token_due_datetime = \
                        fields.Datetime.now()
                    raise UserError(_(
                        u"Erro na obtenção do Token de acesso à Api. %s"
                    ) % str(e))
                finally:
                    record.create_bank_api_operation(
                        token_request,
                        operation_type='token_request',
                        environment=environment,
                    )
                    self._cr.commit()

            for boleto in boleto_list:
                ApiItau.convert_to(boleto, tipo_ambiente=environment)
                response = False
                try:
                    response = boleto.post(token, itau_key, barcode_endpoint)
                    if response.ok:
                        # ambiente = 1 --> HML
                        if boleto.tipo_ambiente == '1':
                            receivable_ids.write({
                                'state_cnab': 'accepted_hml'
                            })
                        # PROD
                        else:
                            receivable_ids.write({
                                'state_cnab': 'accepted',
                                'situacao_pagamento': 'aberta'
                            })
                    else:
                        receivable_ids.write({
                            'state_cnab': 'not_accepted'
                        })

                except Exception as e:
                    raise UserError(_(
                        u"Erro ao registrar a fatura boleto. Verifique se as "
                        u"configurações da API estão corretas. %s"
                    ) % str(e))

                finally:
                    record.create_bank_api_operation(
                        response,
                        operation_type='invoice_register',
                        environment=environment,
                    )
        self.message_post(_(
            "Comunicação com o banco via API concluída. Verifique a Aba "
            "'Operações Bancárias' consultar o resultado do processamento."
        ))

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
                inv_number = inv.get_invoice_fiscal_number().split(
                    '/')[-1].zfill(8)
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
                instrucoes = ''
                if inv.eval_payment_mode_instrucoes:
                    instrucoes = inv.eval_payment_mode_instrucoes + '\n'
                if inv.instrucoes:
                    instrucoes += inv.instrucoes + '\n'
                interval.instrucoes = instrucoes

        return result


    @api.multi
    def create_account_payment_line_baixa(self):

        for inv in self:

            applicable_lines = inv.move_id.line_ids.filtered(
                lambda x: (
                        x.payment_mode_id.payment_order_ok and
                        x.account_id.internal_type in ('receivable', 'payable')
                )
            )

            if not applicable_lines:
                raise UserError(_(
                    'No Payment Line created for invoice %s because '
                    'it\'s internal type isn\'t receivable or payable.') %
                                inv.number)

            payment_modes = applicable_lines.mapped('payment_mode_id')
            if not payment_modes:
                raise UserError(_(
                    "No Payment Mode on invoice %s") % inv.number)

            result_payorder_ids = []
            apoo = self.env['account.payment.order']
            for payment_mode in payment_modes:
                payorder = apoo.search([
                    ('payment_mode_id', '=', payment_mode.id),
                    ('state', '=', 'draft')
                ], limit=1)

                new_payorder = False
                if not payorder:
                    payorder = apoo.create(inv._prepare_new_payment_order(
                        payment_mode
                    ))
                    new_payorder = True
                result_payorder_ids.append(payorder.id)
                action_payment_type = payorder.payment_type
                count = 0
                for line in applicable_lines.filtered(
                        lambda x: x.payment_mode_id == payment_mode
                ):
                    line.create_payment_line_from_move_line(payorder)
                    count += 1
                if new_payorder:
                    inv.message_post(_(
                        '%d payment lines added to the new draft payment '
                        'order %s which has been automatically created.')
                                     % (count, payorder.name))
                else:
                    inv.message_post(_(
                        '%d payment lines added to the existing draft '
                        'payment order %s.')
                                     % (count, payorder.name))

    @api.multi
    def invoice_validate(self):
        result = super(AccountInvoice, self).invoice_validate()
        self.create_account_payment_line()
        return result
