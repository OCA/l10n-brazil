# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountInvoiceAPIConfirm(models.TransientModel):
    """
    Esse wizard é utilizado para seleção de faturas a serem registradas no
    banco via API
    """

    _name = "account.invoice.api.confirm"
    _description = "Registrar as faturas selecionadas via API"

    environment = fields.Char(
        string='Ambiente',
        default=lambda self: self._default_environment(),
    )

    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        string='Faturas',
        default=lambda self: self._default_invoice_ids(),
    )

    @api.model
    def _default_invoice_ids(self):
        active_ids = self.env['account.invoice'].browse(
            self._context.get('active_ids'))

        return active_ids.search([
            ('id', 'in', active_ids.ids),
            ('state', '=', 'open'),
            ('eval_state_cnab', 'not in', (
                'added_paid', 'accepted', 'done', 'accepted_hml'))
        ]).ids

    @api.model
    def _default_environment(self):
        active_ids = self.env['account.invoice'].browse(
            self._context.get('active_ids'))
        environment = active_ids[:1].partner_id.company_id.environment
        if not environment:
            message = "Nenhum ambiente está configurado no cadastro da " \
                      "empresa. Favor escolher entre Produção e Homologação."
            _logger.error(message)
            raise UserError(message)

        try:
            environment_text = self.env['res.company']._fields.get(
                'environment').selection[int(environment) - 1][-1]
        except Exception as e:
            message = 'Erro ao obter ambiente. %s' % str(e)
            _logger.error(message)
            raise UserError(message)

        return environment_text

    @api.multi
    def api_register_confirm(self):
        # TODO: Redundant code
        for record in self:
            if len(record.invoice_ids) > 1:
                for invoice_id in record.invoice_ids:
                    try:
                        invoice_id.with_delay().register_invoice_api()
                    except Exception as e:
                        _logger.debug('Erro ao processar fatura %s. %s' % (
                            invoice_id.number, str(e)))
            else:
                for invoice_id in record.invoice_ids:
                    try:
                        invoice_id.register_invoice_api()
                    except Exception as e:
                        _logger.debug('Erro ao processar fatura %s. %s' % (
                            invoice_id.number, str(e)))