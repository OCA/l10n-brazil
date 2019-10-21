# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    cce_document_event_ids = fields.One2many(
        'l10n_br_account.invoice.cce', 'invoice_id', u'Eventos')
    is_edoc_printed = fields.Boolean(
        string="Danfe Impresso",
        readonly=True,
    )

    def _edoc(self):
        pass

    def edoc_export(self):
        for record in self:
            record._edoc_export()
            record.state = 'sefaz_export'

    def action_confirm_invoice(self):
        self.nfe_check()
        self.action_date_assign()
        self.action_number()
        self.action_move_create()
        self.edoc_export()
        return True

    def action_edoc_send(self):
        pass

    @api.multi
    def action_edoc_cancel(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.nfe_protocol_number
        emitente = self.issuer

        if ((document_serie_id and fiscal_document_id and not electronic) or
            not nfe_protocol) or emitente == u'1':
            return self.action_cancel()
        else:
            result = self.env['ir.actions.act_window'].for_xml_id(
                'edoc_base',
                'edoc_cancel_wizard_act_window'
            )
            return result

    @api.multi
    def action_edoc_cce(self):
        self.ensure_one()
        document_serie_id = self.document_serie_id
        fiscal_document_id = self.document_serie_id.fiscal_document_id
        electronic = self.document_serie_id.fiscal_document_id.electronic
        nfe_protocol = self.nfe_protocol_number
        emitente = self.issuer

        if ((document_serie_id and fiscal_document_id and not electronic) or
            not nfe_protocol) or emitente == u'1':
            raise UserError(_(
                "Impossível enviar uma cartão de correção !!!\n"
                "Para uma nota fiscal não emitida / não eletônica"
            ))
        else:
            result = self.env['ir.actions.act_window'].for_xml_id(
                'edoc_base',
                'edoc_cce_wizard_act_window'
            )
            return result