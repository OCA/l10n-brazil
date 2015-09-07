# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    Thinkopen - Brasil
#    Copyright (C) Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
#    Akretion
#    Copyright (C) Akretion (<http://www.akretion.com>)
#    KMEE
#    Copyright (C) KMEE (<http://www.kmee.com.br>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import re
from openerp import models, fields, api


class ResCompany(models.Model):

    _inherit = 'res.company'

    # BUG: O super cotinua sendo chamado.
    @api.one
    def _get_address_data(self):
        self.l10n_br_city_id = self.partner_id.l10n_br_city_id
        self.district = self.partner_id.district
        self.number = self.partner_id.number

    @api.one
    def _get_l10n_br_data(self):
        """ Read the l10n_br specific functional fields. """
        self.legal_name = self.partner_id.legal_name
        self.cnpj_cpf = self.partner_id.cnpj_cpf
        self.inscr_est = self.partner_id.inscr_est
        self.inscr_mun = self.partner_id.inscr_mun
        self.suframa = self.partner_id.suframa

    @api.one
    def _set_l10n_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.suframa = self.suframa

    @api.one
    def _set_l10n_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.legal_name = self.legal_name

    @api.one
    def _set_l10n_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.cnpj_cpf = self.cnpj_cpf

    @api.one
    def _set_l10n_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.inscr_est = self.inscr_est

    @api.one
    def _set_l10n_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.inscr_mun = self.inscr_mun

    @api.one
    def _set_l10n_br_number(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.number = self.number

    @api.one
    def _set_l10n_br_district(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.district = self.district

    @api.one
    def _set_l10n_br_city_id(self):
        """ Write the l10n_br specific functional fields. """
        self.partner_id.l10n_br_city_id = self.l10n_br_city_id

    cnpj_cpf = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_cnpj_cpf, size=18,
        string='CNPJ')

    inscr_est = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_inscr_est, size=16,
        string='Inscr. Estadual')

    inscr_mun = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_inscr_mun, size=18,
        string='Inscr. Municipal')

    suframa = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_suframa, size=18,
        string='Suframa')

    legal_name = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_legal_name, size=128,
        string=u'Razão Social')

    l10n_br_city_id = fields.Many2one(
        compute=_get_address_data, inverse='_set_l10n_br_city_id',
        comodel_name='l10n_br_base.city', string="City", multi='address')

    district = fields.Char(
        compute=_get_address_data, inverse='_set_l10n_br_district', size=32,
        string="Bairro", multi='address')

    number = fields.Char(
        compute=_get_address_data, inverse='_set_l10n_br_number', size=10,
        string=u"Número", multi='address')

    @api.onchange('cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        if self.cnpj_cpf:
            val = re.sub('[^0-9]', '', self.cnpj_cpf)
            if len(val) == 14:
                cnpj_cpf = "%s.%s.%s/%s-%s"\
                    % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])
            self.cnpj_cpf = cnpj_cpf

    @api.onchange('l10n_br_city_id')
    def onchange_l10n_br_city_id(self):
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
            self.l10n_br_city_id = self.l10n_br_city_id

    @api.onchange('zip')
    def onchange_mask_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                zip = "%s-%s" % (val[0:5], val[5:8])
                self.zip = zip
