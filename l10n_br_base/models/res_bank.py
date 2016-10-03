# -*- coding: utf-8 -*-
#    Copyright (C) 2016 MultidadosTI (http://www.multidadosti.com.br)
#    @author Michell Stuttgart <michellstut@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
import re


class ResBank(models.Model):

    _inherit = 'res.bank'

    district = fields.Char(u'Bairro', size=32)
    number = fields.Char(u'Número', size=10)
    country_id = fields.Many2one('res.country', u'País')

    state_id = fields.Many2one('res.country.state', u'Estado',
                               domain="[('country_id','=',country_id)]")

    l10n_br_city_id = fields.Many2one('l10n_br_base.city', u'Municipio',
                                      domain="[('state_id','=',state_id)]")

    @api.onchange('l10n_br_city_id')
    def _onchange_l10n_br_city_id(self):
        """ Ao alterar o campo l10n_br_city_id que é um campo relacional
        com o l10n_br_base.city que são os municípios do IBGE, copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        if self.l10n_br_city_id:
            self.city = self.l10n_br_city_id.name

    @api.onchange('state_id')
    def _onchange_state_id(self):
        """ Ao alterar o campo state_id que é um campo relacional
        com o res.country.state, copia o nome do estado para o
        campo state que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo state.
        """
        if self.state_id:
            self.state = self.state_id

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """ Ao alterar o campo country_id que é um campo relacional
        com o res.country.state, copia o nome do país para o
        campo country que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo country.
        """
        if self.country_id:
            self.country = self.country_id

    @api.onchange('zip')
    def _onchange_zip(self):
        if self.zip:
            val = re.sub('[^0-9]', '', self.zip)
            if len(val) == 8:
                self.zip = "%s-%s" % (val[0:5], val[5:8])
