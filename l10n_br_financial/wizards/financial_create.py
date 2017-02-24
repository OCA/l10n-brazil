# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons.l10n_br_financial.models.financial_move_model import (
    FINANCIAL_MOVE
)


class FinancialMoveCreate(models.TransientModel):

    _name = 'financial.move.create'
    _inherit = ['financial.move.model']

#    def __init__(self, cr, uid):
#        self.lines = False

    def _readonly_state(self):
        return {
            'draft': [('readonly', False)],
            'computed': [('readonly', False)],
        }

    # document_date = fields.Date(
    #     string=u"Document date",
    #     # required=True,
    #     # readonly=True,
    #     # states=_readonly_state,
    #     # track_visibility='onchange',
    # )
    # document_number = fields.Char(
    #     string=u"Document Nº",
    #     # required=True,
    #     # readonly=True,
    #     # states=_readonly_state,
    #     # track_visibility='onchange',
    # )
    # amount_document = fields.Monetary(
    #     string=u"Document amount",
    #     # required=True,
    #     # readonly=True,
    #     # states=_readonly_state,
    #     # track_visibility='onchange',
    # )

    move_type = fields.Selection(
        selection=FINANCIAL_MOVE
    )
    payment_mode = fields.Many2one(
        comodel_name='account.payment.mode',  # FIXME:
        #track_visibility='onchange',
    )
    payment_term = fields.Many2one(
        comodel_name='account.payment.term',  # FIXME:
        #track_visibility='onchange',
    )
    line_ids = fields.One2many(
        comodel_name='financial.move.line.create',
        inverse_name='financial_move_id',
        #readonly=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', u'Draft'),
            ('computed', u'Computed'),
        ],
        string='Status',
        index=True,
        readonly=True,
        default='draft',
        track_visibility='onchange',
        copy=False,
    )

    @api.onchange('payment_term', 'document_number', 'document_date', 'amount_document')
    def onchange_fields(self):
        res = {}

        if not (self.payment_term and self.document_number and
                self.document_date and self.amount_document > 0.00):
            return res

        payment_line = self.env['financial.move.line.create']
        computations = self.payment_term.compute(self.amount_document, self.document_date)

        #payment_ids = [
        #    [5, False, {}],
        #]
        payment_ids = []
        for idx, item in enumerate(computations[0]):
            payment = dict(
                document_item=self.document_number + '/' + str(idx + 1),
                due_date=item[0],
                amount_document=item[1],
                #financial_move_id=self.id,
            )
            payment_ids.append((0, False, payment))
            #payment_line.create(payment)
        #self.lines = payment_ids
        #res['value'] = {'line_ids': payment_ids}
        self.line_ids = payment_ids
        #return res

    @api.multi
    def compute(self):
        #import wdb; wdb.set_trace() # BREAKPOINT
        financial_move = self.env['financial.move']
        for record in self:
            #financial_move_lines = self.env['financial.move.line.create']
            #lines = self.line_ids
            #lines = self.lines
            #lines = financial_move_lines.search([('financial_move_id', '=', self.id)])
            #no financial.move
            moves = []
            for move in record.line_ids:
                move_id = financial_move.create(dict(
                    company_id=self.company_id.id,
                    currency_id=self.currency_id.id,
                    move_type=self.move_type,
                    partner_id=self.partner_id.id,
                    document_number=self.document_number,
                    document_date=self.document_date,
                    payment_mode=self.payment_mode.id,
                    payment_term=self.payment_term.id,
                    document_item=move.document_item,
                    due_date=move.due_date,
                    amount_document=move.amount_document,
                ))
                moves.append(move_id.id)

        if record.move_type == 'r':
            action = 'financial_receivable_act_window'
        else:
            action = 'financial_payable_act_window'
        action = {
            'type': 'ir.actions.act_window',
            'name': action,
            'res_model': 'financial.move',
            'domain': [('id', '=', moves)],
            'view_mode': 'tree,form',
        }
        return action

    @api.multi
    def doit(self):
        for wizard in self:
            # fm = self.env['financial.move']
            # TODO
            pass

        if wizard.move_type == 'r':
            action = 'financial_receivable_act_window'
        else:
            action = 'financial_payable_act_window'
        action = {
            'type': 'ir.actions.act_window',
            'name': action,  # TODO
            'res_model': 'financial.move',
            # 'domain': [('id', '=', result_ids)],f
            'view_mode': 'tree,form',
        }
        return action


class FinancialMoveLineCreate(models.TransientModel):

    _name = 'financial.move.line.create'
    #_inherit = ['financial.move.model']

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        #required=True,
        #readonly=True,
        #states=_readonly_state,
        #track_visibility='onchange',
        #default=_default_currency,
    )

    document_item = fields.Char(
        string=u"Document item",
    )

    document_date = fields.Date(
        string=u"Document date",
        #required=True,
        #readonly=True,
        #states=_readonly_state,
        #track_visibility='onchange',
    )

    due_date = fields.Date(
        string=u"Due date",
        #required=True,
        #readonly=True,
        #states=_readonly_state,
        #track_visibility='onchange',
    )

    amount_document = fields.Monetary(
        string=u"Document amount",
        #required=True,
        #readonly=True,
        #states=_readonly_state,
        #track_visibility='onchange',
    )

    financial_move_id = fields.Many2one(
        comodel_name='financial.move.create',
        required=True
    )
