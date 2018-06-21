# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions
from openerp.exceptions import ValidationError
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao


class ResCompany(models.Model):

    _inherit = 'res.company'

    eh_empresa_base = fields.Boolean(
        string='É Empresa Base?',
        compute='_compute_empresa_base',
        store=True,
    )
    matriz = fields.Many2one(
        string='Matriz',
        comodel_name='res.company',
        compute='_compute_matriz',
        store=True,
    )

    @api.depends('cnpj_cpf')
    def _compute_empresa_base(self):
        for empresa in self:
            empresa.eh_empresa_base = ('0001-' in empresa.cnpj_cpf)

    @api.depends('cnpj_cpf')
    def _compute_matriz(self):
        for empresa in self:
            matriz = False
            if not empresa.eh_empresa_base:
                matriz = self.env['res.company'].search([
                    ('cnpj_cpf', 'like', empresa.cnpj_cpf[0:10] + '/0001-')
                ], limit=1)
            empresa.matriz = matriz