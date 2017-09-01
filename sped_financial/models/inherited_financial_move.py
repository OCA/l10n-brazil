# -*- coding: utf-8 -*-
#
#  Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from openerp.addons.l10n_br_base.models.sped_base import SpedBase


class FinancialMove(SpedBase, models.Model):
    _inherit = 'financial.move'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string='Destinatário/Remetente'
    )
    doc_source_id = fields.Reference(
        selection_add=[('sped.documento', 'Documento Fiscal')],
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
        ondelete='restrict',
    )
    documento_duplicata_id = fields.Many2one(
        comodel_name='sped.documento.duplicata',
        string='Duplicata do Documento Fiscal',
        ondelete='restrict',
    )

    @api.depends('date_maturity')
    def _compute_date_business_maturity(self):
        for move in self:
            if (not move.date_maturity) or \
                (not move.company_id.country_id) or \
                (move.company_id.country_id.id != self.env.ref('base.br').id):
                super(FinancialMove, move)._compute_date_business_maturity()
                continue

            date_maturity = fields.Date.from_string(move.date_maturity)
            date_business_maturity = \
                self.env['resource.calendar'].proximo_dia_util_bancario(
                    date_maturity
                )
            move.date_business_maturity = date_business_maturity

    def _sincroniza_empresa_company_participante_partner(self):
        for documento in self:
            documento.company_id = documento.empresa_id.company_id
            documento.partner_id = documento.participante_id.partner_id

    @api.onchange('empresa_id', 'participante_id')
    def _onchange_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.depends('empresa_id', 'participante_id')
    def _depends_empresa_participante(self):
        self._sincroniza_empresa_company_participante_partner()

    @api.model
    def create(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(FinancialMovet, self).create(dados)

    @api.model
    def write(self, dados):
        dados = self._mantem_sincronia_cadastros(dados)
        return super(FinancialMovet, self).write(dados)
