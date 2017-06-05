# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

import logging

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError

from odoo.addons.l10n_br_base.constante_tributaria import (
    MODELO_FISCAL_EMISSAO_PRODUTO,
    MODELO_FISCAL_EMISSAO_SERVICO,
)
from openerp.addons.l10n_br_base.models.sped_base import (
    SpedBase
)


class SpedCalculoImposto(SpedBase):
    """ Definie informações essenciais para as operações brasileiras"""

    _abstract = False

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get(self._name)

    @api.depends('company_id', 'partner_id')
    def _compute_is_brazilian(self):
        for invoice in self:
            if invoice.company_id.country_id:
                if invoice.company_id.country_id.id == \
                        self.env.ref('base.br').id:
                    invoice.is_brazilian = True

                    if invoice.partner_id.sped_participante_id:
                        invoice.sped_participante_id = \
                            invoice.partner_id.sped_participante_id
                    continue
            invoice.is_brazilian = False

    is_brazilian = fields.Boolean(
        string=u'Is a Brazilian?',
        compute='_compute_is_brazilian',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=_default_company_id,
    )
    sped_empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        related='company_id.sped_empresa_id',
        string='Empresa',
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
    )
    sped_participante_id = fields.Many2one(
        comodel_name='sped.participante',
        string=u'Destinatário/Remetente'
    )
    sped_operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação Fiscal (produtos)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_PRODUTO)],
    )
    sped_operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string=u'Operação Fiscal (serviços)',
        domain=[('modelo', 'in', MODELO_FISCAL_EMISSAO_SERVICO)],
    )
    condicao_pagamento_id = fields.Many2one(
        comodel_name='account.payment.term',
        string='Condição de pagamento',
        domain=[('forma_pagamento', '!=', False)],
    )

    @api.onchange('condicao_pagamento_id')
    def _onchange_condicao_pagamento_id(self):
        self.ensure_one()
        self.payment_term_id = self.condicao_pagamento_id

    @api.onchange('sped_participante_id')
    def _onchange_sped_participante_id(self):
        self.ensure_one()
        self.partner_id = self.sped_participante_id.partner_id
