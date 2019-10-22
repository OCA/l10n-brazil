# -*- coding: utf-8 -*-
# Copyright 2019 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def _search(
            self, args, offset=0, limit=None, order=None, count=False,
            access_rights_uid=None):
        result = super(IrAttachment, self)._search(
            args, offset, limit, order, count, access_rights_uid
        )

        data = {}
        for arg in args:
            if type(arg) == tuple:
                field, expression, values = arg
                data[field] = (expression, values)

        if (data.get('res_model') and
                data.get('res_model')[1] == 'account.invoice'):
            res_id = data.get('res_id')[1]
            if res_id:
                invoice_ids = self.env['account.invoice'].browse(res_id)
                result += (
                        invoice_ids.mapped('file_xml_autorizacao_id').ids +
                        invoice_ids.mapped(
                            'file_xml_autorizacao_cancelamento_id').ids +
                        invoice_ids.mapped('file_pdf_id').ids
                )
        return result


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # Sim isso esta duplicado
    # Todos os eventos
    account_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.document_event',
        inverse_name='document_event_ids',
        string=u'Eventos'
    )
    # Eventos de envio
    autorizacao_event_id = fields.Many2one(
        comodel_name='l10n_br_account.document_event',
        string='Autorização',
        readonly=True,
    )
    file_xml_id = fields.Many2one(
        comodel_name='ir.attachment',
        related='autorizacao_event_id.xml_sent_id',
        string='XML',
        ondelete='restrict',
        copy=False,
        readonly=True,
    )
    file_xml_autorizacao_id = fields.Many2one(
        comodel_name='ir.attachment',
        related='autorizacao_event_id.xml_returned_id',
        string='XML de autorização',
        ondelete='restrict',
        copy=False,
        readonly=True,
    )
    # Eventos de cancelamento
    cancel_document_event_id = fields.Many2one(
        comodel_name='l10n_br_account.invoice.cancel',
        string='Cancelamento'
    )
    # Eventos de carta de correção
    cce_document_event_ids = fields.One2many(
        comodel_name='l10n_br_account.invoice.cce',
        inverse_name='invoice_id',
        string=u'Eventos '
    )

    is_edoc_printed = fields.Boolean(
        string="Danfe Impresso",
        readonly=True,
    )

    file_xml_cancelamento_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de cancelamento',
        ondelete='restrict',
        copy=False,
    )
    file_xml_autorizacao_cancelamento_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='XML de autorização de cancelamento',
        ondelete='restrict',
        copy=False,
    )
    file_pdf_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='PDF DANFE/DANFCE',
        ondelete='restrict',
        copy=False,
    )

    # file_autorizacao_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )
    #
    # file_ids = fields.Many2many(
    #     comodel_name='ir.attachment',
    #     compute='_compute_files',
    # )

    def _gerar_evento(self, arquivo_xml, type):
        event_obj = self.env['l10n_br_account.document_event']
        event_id = event_obj.create({
            'type': type,
            'company_id': self.company_id.id,
            'origin': self.fiscal_document_id.code + '/' + self.fiscal_number,
            'create_date': fields.Datetime.now(),
            'document_event_ids': self.id
        })
        event_id._grava_anexo(arquivo_xml, 'xml')
        return event_id

    def _edoc_export(self):
        pass

    def edoc_export(self):
        for record in self:
            record._edoc_export()
            record.state = 'sefaz_export'

    def action_edoc_confirm(self):
        self.nfe_check()
        self.action_date_assign()
        self.action_number()
        self.action_move_create()
        self.edoc_export()
        return True

    def _edoc_send(self):
        self.write({'state': 'sefaz_export'})

    def action_edoc_send(self):
        for record in self:
            record._edoc_send()

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
