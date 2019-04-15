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
from odoo.tools import config


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _get_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """

        for obj in self:
            obj.legal_name = obj.partner_id.legal_name
            obj.cnpj_cpf = obj.partner_id.cnpj_cpf
            obj.number = obj.partner_id.number
            obj.district = obj.partner_id.district
            obj.l10n_br_city_id = obj.partner_id.l10n_br_city_id
            obj.inscr_est = obj.partner_id.inscr_est
            obj.inscr_mun = obj.partner_id.inscr_mun
            obj.suframa = obj.partner_id.suframa
            other_inscr_est_lines = self.env['other.inscricoes.estaduais']
            for inscr_est_line in obj.partner_id.other_inscr_est_lines:
                other_inscr_est_lines |= inscr_est_line
            obj.other_inscr_est_lines = other_inscr_est_lines

    @api.multi
    def _set_l10n_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.legal_name = self.legal_name

    @api.multi
    def _set_l10n_br_number(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.number = self.number

    @api.multi
    def _set_l10n_br_district(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.district = self.district

    @api.multi
    def _set_l10n_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.cnpj_cpf = self.cnpj_cpf

    @api.multi
    def _set_l10n_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.inscr_est = self.inscr_est

    @api.multi
    def _set_l10n_br_other_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        for record in self:
            other_inscr_est_lines = self.env['other.inscricoes.estaduais']
            for inscr_est_line in record.other_inscr_est_lines:
                other_inscr_est_lines |= inscr_est_line
            record.partner_id.other_inscr_est_lines = other_inscr_est_lines

    @api.multi
    def _set_l10n_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.inscr_mun = self.inscr_mun

    @api.multi
    def _set_l10n_br_city_id(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.l10n_br_city_id = self.l10n_br_city_id

    @api.multi
    def _set_l10n_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        self.ensure_one()
        self.partner_id.suframa = self.suframa

    legal_name = fields.Char(
        string=u'Razão Social',
        compute=_get_l10n_br_data,
        inverse=_set_l10n_br_legal_name,
        size=128)

    district = fields.Char(
        compute=_get_l10n_br_data,
        string=u'Bairro',
        inverse=_set_l10n_br_district,
        size=32,
        multi='address')

    number = fields.Char(
        compute=_get_l10n_br_data,
        string=u'Número',
        inverse=_set_l10n_br_number,
        size=10,
        multi='address')

    cnpj_cpf = fields.Char(
        compute=_get_l10n_br_data,
        string='CNPJ/CPF',
        inverse=_set_l10n_br_cnpj_cpf,
        size=18)

    inscr_est = fields.Char(
        compute=_get_l10n_br_data,
        string=u'Inscr. Estadual',
        inverse=_set_l10n_br_inscr_est,
        size=16)

    other_inscr_est_lines = fields.One2many(
        'other.inscricoes.estaduais', 'partner_id',
        compute=_get_l10n_br_data, inverse=_set_l10n_br_other_inscr_est,
        string=u'Outras Inscrições Estaduais', ondelete='cascade'
    )

    inscr_mun = fields.Char(
        compute=_get_l10n_br_data,
        string=u'Inscr. Municipal',
        inverse=_set_l10n_br_inscr_mun,
        size=18)

    suframa = fields.Char(
        compute=_get_l10n_br_data,
        string='Suframa',
        inverse=_set_l10n_br_suframa,
        size=18)

    l10n_br_city_id = fields.Many2one(
        comodel_name='l10n_br_base.city',
        string=u'Municipio',
        domain="[('state_id', '=', state_id)]",
        compute=_get_l10n_br_data,
        inverse=_set_l10n_br_city_id)

    @api.onchange('cnpj_cpf')
    def _onchange_cnpj_cpf(self):
        country_code = self.country_id.code or ''
        if self.cnpj_cpf and country_code.upper() == 'BR':
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if len(val) == 14:
                self.cnpj_cpf = "%s.%s.%s/%s-%s" % (
                    val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])

    @api.onchange('l10n_br_city_id')
    def _onchange_l10n_br_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.

        param int l10n_br_city_id: id do l10n_br_city_id digitado.

        return: dicionário com o nome e id do município.
        """
        if self.l10n_br_city_id:
            self.city = self.l10n_br_city_id.name

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])

    @api.onchange('state_id')
    def _onchange_state_id(self):
        for record in self:
            record.inscr_est = None

    @api.multi
    def write(self, values):
        try:
            result = super(ResCompany, self).write(values)
        except Exception:
            if not config['without_demo'] and values.get('currency_id'):
                result = models.Model.write(self, values)
            else:
                raise

        return result
