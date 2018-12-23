# -*- coding: utf-8 -*-
#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

from ..tools import misc


class ResBank(models.Model):
    _inherit = 'res.bank'

    district = fields.Char(
        string=u'District',
        size=32)

    street_number = fields.Char(
        string=u'Number',
        size=10)

    city_id = fields.Many2one(
        comodel_name='res.city',
        string=u'City',
        domain="[('state_id', '=', state)]")

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        self.city = self.city_id.name

    @api.onchange('zip')
    def _onchange_zip(self):
        self.zip = misc.format_zipcode(self.zip,
                                       self.country_id.code)
