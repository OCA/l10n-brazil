# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job

from pyboleto.bank_api.itau import ApiItau

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

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

            itau_key = company_id.itau_key
            barcode_endpoint = company_id.raiz_endpoint
            environment = company_id.environment

            token = record.obtain_token(company_id, environment)

            for boleto in boleto_list:
                ApiItau.convert_to(boleto, tipo_ambiente=environment)
                response = False
                try:
                    response = boleto.post(token, itau_key, barcode_endpoint)
                    if response and response.ok:
                        # Remove Invoice from debit.orders
                        record._remove_payment_order_line(_raise=False)

                        # Create new Debit Order for payment_order_line
                        try:
                            record.create_api_account_payment_line()

                        except Exception as e:
                            _logger.debug(str(e))
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
                    if response and response.ok:
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

                    record.create_bank_api_operation(
                        response,
                        operation_type='invoice_register',
                        environment=environment,
                    )
        self.message_post(_(
            "Comunicação com o banco via API concluída. Verifique a Aba "
            "'Operações Bancárias' consultar o resultado do processamento."
        ))

    def obtain_token(self, company_id, environment):
        """
        Método para buscar ou atualizar o Token da empresa
        :param company_id: Empresa
        :param environment: Ambiente da operação
        :return: O Token da empresa
        """

        token = company_id.api_itau_token
        if not token or company_id.api_itau_token_due_datetime <= \
                fields.Datetime.now():

            client_id = company_id.client_id
            client_secret = company_id.client_secret
            endpoint = company_id.api_endpoint

            token_request = False
            try:
                token_request = ApiItau.generate_api_key(
                    client_id, client_secret, endpoint)
                token_request_dict = json.loads(token_request.content)
                token = token_request_dict.get('access_token')
                company_id.api_itau_token = token
                company_id.api_itau_token_due_datetime = \
                    fields.Datetime.context_timestamp(
                        self, datetime.now()) + relativedelta(
                        seconds=token_request_dict.get('expires_in'))

            except Exception as e:
                company_id.api_itau_token = ''
                company_id.api_itau_token_due_datetime = \
                    fields.Datetime.now()
                raise UserError(_(
                    u"Erro na obtenção do Token de acesso à Api. %s"
                ) % str(e))
            finally:
                self.create_bank_api_operation(
                    token_request,
                    operation_type='token_request',
                    environment=environment,
                )
                self._cr.commit()

        return token
