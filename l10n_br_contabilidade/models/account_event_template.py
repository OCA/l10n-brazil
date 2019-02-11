# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import Warning


class AccountEventTemplate(models.Model):
    _name = 'account.event.template'

    name = fields.Char(
        string='Nome',
    )

    lote_lancamento_id = fields.Many2one(
        string=u'Lote de Lançamentos',
        comodel_name='account.journal',
    )

    account_formula = fields.Selection(
        string=u'Fórmula',
        selection=[
            (1, '1ª Fórmula'),
            (2, '2ª Fórmula'),
            (3, '3ª Fórmula'),
            (4, '4ª Fórmula'),
        ],
    )

    account_event_template_line_ids = fields.One2many(
        string='Partidas',
        comodel_name='account.event.template.line',
        inverse_name='account_event_template_id',
    )

    def validar_primeira_formula(self):
        if self.account_formula == 1:
            for partida in self.account_event_template_line_ids:
                if not partida.account_debito_id or not partida.account_credito_id:
                    raise Warning(
                        'Nos lançamentos de 1ª Fórmula é '
                        'necessário que todas as partidas possuam uma '
                        'conta de débito e uma de crédito!'
                    )

    def validar_formula_roteiro_contabil(self):
        self.validar_primeira_formula()

    @api.model
    def create(self, vals):
        res = super(AccountEventTemplate, self).create(vals)

        res.validar_formula_roteiro_contabil()

        return res

    @api.multi
    def write(self, vals):
        res = super(AccountEventTemplate, self).create(vals)

        self.validar_formula_roteiro_contabil()

        return res
