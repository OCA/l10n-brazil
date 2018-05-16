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
from ..constante_tributaria import (
    INDICADOR_IE_DESTINATARIO,
    REGIME_TRIBUTARIO,
    REGIME_TRIBUTARIO_SIMPLES,
)


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
        u'Razão Social', size=60,
        help="Nome utilizado em documentos fiscais")

    eh_consumidor_final = fields.Boolean(
        string='É consumidor final?',
    )

    eh_orgao_publico = fields.Boolean(
        string='É órgão público?',
    )

    eh_transportadora = fields.Boolean(
        string='É transportadora?',
    )

    contribuinte = fields.Selection(
        selection=INDICADOR_IE_DESTINATARIO,
        string='Contribuinte',
        # required=True,
    )

    regime_tributario = fields.Selection(
        selection=REGIME_TRIBUTARIO,
        string='Regime tributário',
        default=REGIME_TRIBUTARIO_SIMPLES,
        index=True,
    )

    crc = fields.Char(
        string='Conselho Regional de Contabilidade',
        size=14
    )

    crc_uf = fields.Many2one(
        comodel_name='res.country.state',
        string='UF do CRC',
        ondelete='restrict'
    )

    rntrc = fields.Char(
        string='RNTRC',
        size=15
    )

    cei = fields.Char(
        string='CEI',
        size=15
    )

    legal_name = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_legal_name,
        size=128, string=u'Razão Social')

    district = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_district, size=32,
        string="Bairro", multi='address')

    number = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_number, size=10,
        string=u"Número", multi='address')

    cnpj_cpf = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_cnpj_cpf,
        size=18, string='CNPJ/CPF')

    inscr_est = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_inscr_est,
        size=16, string='Inscr. Estadual')

    inscr_mun = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_inscr_mun,
        size=18, string='Inscr. Municipal')

    suframa = fields.Char(
        compute=_get_l10n_br_data, inverse=_set_l10n_br_suframa,
        size=18, string='Suframa')

    l10n_br_city_id = fields.Many2one(
        'l10n_br_base.city', 'Municipio', domain="[('state_id','=',state_id)]",
        compute=_get_l10n_br_data, inverse=_set_l10n_br_city_id)

    estado = fields.Char(
        string='Estado',
        related='state_id.code',
        index=True
    )
    fantasia = fields.Char(
        string='Fantasia',
        size=60,
        index=True
    )

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

    @api.model
    def create(self, vals):

        company = super(ResCompany, self).create(vals)

        company.inscr_est = vals.get('inscr_est')
        company.cnpj_cpf = vals.get('cnpj_cpf')
        company.state_id = vals.get('state_id')

        return company
