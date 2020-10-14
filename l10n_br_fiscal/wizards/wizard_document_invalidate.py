# Copyright 2019 KMEE
# Copyright (C) 2020  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class InvalidateNumberWizard(models.TransientModel):
    _name = 'l10n_br_fiscal.invalidate.number.wizard'
    _description = 'Invalidate Number Wizard'
    _inherit = 'l10n_br_fiscal.base.wizard.mixin'

    @api.multi
    def doit(self):
        return {'type': 'ir.actions.act_window_close'}

    # TODO
    # @api.multi
    # def doit(self):
    #     for wizard in self:
    #
    #         inut = self.env['l10n_br_fiscal.invalidate.number'].create({
    #             'company_id': document_id.company_id.id,
    #             'fiscal_document_id': document_id.id,
    #             'document_serie_id': document_id.document_serie_id.id,
    #             'number_start': document_id.number,
    #             'number_end': document_id.number,
    #             'state': 'draft',
    #         })
    #         event_id = self.env['l10n_br_fiscal.event'].create({
    #             'type': '3',
    #             'response': 'Inutilização do número %s ao número %s' % (
    #                 document_id.number, document_id.number),
    #             'company_id': document_id.company_id.id,
    #             'origin': 'NFe-%s' % document_id.number,
    #             'date': fields.Datetime.now(),
    #             'state': 'draft',
    #             'invalid_number_document_event_id': inut.id,
    #             'fiscal_document_id': fiscal_document_id.id,
    #         })
    #
    #         inut.invalidate(event_id)
    #     return {"type": "ir.actions.act_window_close"}
