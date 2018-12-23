# -*- coding: utf-8 -*-
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
#    Akretion
#    Copyright (C) Akretion (<http://www.akretion.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import re

from odoo import models, fields, api
from ..tools import misc, fiscal


class Company(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _get_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """

        for obj in self:
            obj.legal_name = obj.partner_id.legal_name
            obj.cnpj_cpf = obj.partner_id.cnpj_cpf
            obj.number = obj.partner_id.number
            obj.district = obj.partner_id.district
            obj.city_id = obj.partner_id.city_id
            obj.inscr_est = obj.partner_id.inscr_est
            obj.inscr_mun = obj.partner_id.inscr_mun
            obj.suframa = obj.partner_id.suframa
            other_inscr_est_lines = self.env['other.inscricoes.estaduais']
            for inscr_est_line in obj.partner_id.other_inscr_est_lines:
                other_inscr_est_lines |= inscr_est_line
            obj.other_inscr_est_lines = other_inscr_est_lines

    def _inverse_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.legal_name = company.legal_name

    def _inverse_street_number(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.number = company.number

    def _inverse_district(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.district = company.district

    def _inverse_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.cnpj_cpf = company.cnpj_cpf

    def _inverse_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_est = company.inscr_est

    def _inverse_other_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            other_inscr_est_lines = self.env['other.inscricoes.estaduais']
            for ies in company.other_inscr_est_lines:
                other_inscr_est_lines |= ies
            company.partner_id.other_inscr_est_lines = other_inscr_est_lines

    def _inverse_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_mun = company.inscr_mun

    def _inverse_city_id(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.city_id = company.city_id

    def _inverse_suframa(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.suframa = company.suframa

    legal_name = fields.Char(
        string='Legal Name',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_legal_name',
        size=128)

    district = fields.Char(
        string='District',
        compute='_get_l10n_br_data,
        inverse='_set_l10n_br_district',
        size=32)

    street_number = fields.Char(
        string='Number',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_number',
        size=10)

    city_id = fields.Many2one(
        string='City',
        comodel_name='res.city',
        domain="[('state_id', '=', state_id)]",
        compute='_get_l10n_br_data',
        inverse='_inverse_city_id')

    cnpj_cpf = fields.Char(
        string='CNPJ/CPF',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_cnpj_cpf',
        size=18)

    inscr_est = fields.Char(
        string='State Tax Number',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_inscr_est',
        size=16)

    state_tax_number_ids = fields.One2many(
        string='State tax numbers'
        comodel_name='state.tax.numbers',
        string='partner_id',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_other_inscr_est',
        ondelete='cascade'
    )

    inscr_mun = fields.Char(
        string=u'Municipal Tax Number',
        compute='_get_l10n_br_data',
        inverse='_set_l10n_br_inscr_mun',
        size=18)

    suframa = fields.Char(
        string='Suframa',
        compute='_get_l10n_br_data',
        inverse='_inverse_suframa',
        size=18)

    @api.onchange('cnpj_cpf')
    def _onchange_cnpj_cpf(self):
        country = self.country_id.code or ''
        self.cnpj_cpf = fiscal.format_cpf_cnpj(self.cnpj_cpf,
                                               country,
                                               True)

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int city_id: id do city_id digitado.

        return: dicionário com o nome e id do município.
        """
        self.city = self.city_id.name

    @api.onchange('zip')
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip,
                                       self.country_id.code)
