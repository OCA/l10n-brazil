# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

import logging
import os
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from pybrasil.data import parse_datetime
    from pybrasil.valor.decimal import Decimal as D

except (ImportError, IOError) as err:
    _logger.debug(err)


DIRNAME = os.path.dirname(__file__)


class SpedIBPTax(models.Model):
    _name = b'sped.ibptax'
    _description = 'IBPTax'
    _order = 'estado_id'
    _rec_name = 'estado_id'

    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
    )
    versao = fields.Char(
        string='Versão',
        size=20,
    )
    data_validade = fields.Date(
        string='Válida até',
    )
    ncm_ids = fields.One2many(
        comodel_name='sped.ibptax.ncm',
        inverse_name='ibptax_id',
        string='NCMs',
    )
    nbs_ids = fields.One2many(
        comodel_name='sped.ibptax.nbs',
        inverse_name='ibptax_id',
        string='NBSs',
    )
    servico_ids = fields.One2many(
        comodel_name='sped.ibptax.servico',
        inverse_name='ibptax_id',
        string='Serviços',
    )

    @api.multi
    def atualizar_tabela(self):
        self.ensure_one()

        sped_ncm = self.env['sped.ncm']
        sped_nbs = self.env['sped.nbs']
        sped_servico = self.env['sped.servico']
        sped_icms = self.env['sped.aliquota.icms.proprio']
        ibptax_ncm = self.env['sped.ibptax.ncm']
        ibptax_nbs = self.env['sped.ibptax.nbs']
        ibptax_servico = self.env['sped.ibptax.servico']

        versao = '17.2.B'
        arquivo = os.path.join(DIRNAME,
                               '../data/ibptax/TabelaIBPTax{uf}{versao}.csv')
        arquivo = arquivo.format(
                uf=self.estado_id.uf, versao=versao)

        ncm_ids = ibptax_ncm.search([('ibptax_id', '=', self.id)])
        ncm_ids.unlink()

        nbs_ids = ibptax_nbs.search([('ibptax_id', '=', self.id)])
        nbs_ids.unlink()

        servico_ids = ibptax_servico.search([('ibptax_id', '=', self.id)])
        servico_ids.unlink()

        arq = open(arquivo, 'r')

        for linha in arq.readlines():
            codigo, ex, tipo, descricao, nacionalfederal, importadosfederal, \
                estadual, municipal, vigenciainicio, vigenciafim, chave, \
                versao, fonte = linha.decode('iso-8859-1').split(';')

            if tipo == '0':
                ncm_ids = sped_ncm.search(
                    [('codigo', '=', codigo), ('ex', '=', ex)])

                if len(ncm_ids) == 0:
                    #dados = {
                        #'codigo': codigo,
                        #'ex': ex,
                        #'descricao': descricao,
                    #}
                    #ncm_ids = sped_ncm.create(dados)
                    continue

                icms_ids = sped_icms.search([('al_icms', '=', D(estadual))])

                dados = {
                    'ibptax_id': self.id,
                    'ncm_id': ncm_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_estadual': D(estadual),
                    'al_icms_id': icms_ids[0].id if len(icms_ids) else False,
                }
                ibptax_ncm.create(dados)

            elif tipo == '1':
                nbs_ids = sped_nbs.search([('codigo', '=', codigo)])

                if len(nbs_ids) == 0:
                    #dados = {
                        #'codigo': codigo,
                        #'descricao': descricao,
                    #}
                    #nbs_ids = sped_nbs.create(dados)
                    continue

                dados = {
                    'ibptax_id': self.id,
                    'nbs_id': nbs_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_municipal': D(municipal),
                }
                ibptax_nbs.create(dados)

            elif tipo == '2' and descricao != 'Vetado':
                servico_ids = sped_servico.search([('codigo', '=', codigo)])

                if len(servico_ids) == 0:
                    #dados = {
                        #'codigo': codigo,
                        #'descricao': descricao,
                    #}
                    #servico_ids = sped_servico.create(dados)
                    continue

                dados = {
                    'ibptax_id': self.id,
                    'servico_id': servico_ids[0].id,
                    'al_ibpt_nacional': D(nacionalfederal),
                    'al_ibpt_internacional': D(importadosfederal),
                    'al_ibpt_municipal': D(municipal),
                }
                ibptax_servico.create(dados)

        arq.close()
        self.data_validade = str(parse_datetime(vigenciafim))[:10]
        self.versao = versao


class SpedIBPTaxNCM(SpedBase, models.Model):
    _name = b'sped.ibptax.ncm'
    _description = 'IBPTax por NCM'

    ibptax_id = fields.Many2one(
        comodel_name='sped.ibptax',
        string='IBPTax',
        ondelete='cascade',
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        related='ibptax_id.estado_id',
        store=True,
    )
    ncm_id = fields.Many2one(
        comodel_name='sped.ncm',
        string='NCM',
    )
    al_ibpt_nacional = fields.Monetary(
        string='Nacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_internacional = fields.Monetary(
        string='Internacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_estadual = fields.Monetary(
        string='Estadual',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_icms_id = fields.Many2one(
        comodel_name='sped.aliquota.icms.proprio',
        string='Estadual',
    )


class SpedIBPTaxNBS(SpedBase, models.Model):
    _name = b'sped.ibptax.nbs'
    _description = 'IBPTax por NBS'

    ibptax_id = fields.Many2one(
        comodel_name='sped.ibptax',
        string='IBPTax',
        ondelete='cascade',
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        related='ibptax_id.estado_id',
        store=True,
    )
    nbs_id = fields.Many2one(
        comodel_name='sped.nbs',
        string='NBS',
    )
    al_ibpt_nacional = fields.Monetary(
        string='Nacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_internacional = fields.Monetary(
        string='Internacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_municipal = fields.Monetary(
        string='Municipal',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )


class SpedIBPTaxServico(SpedBase, models.Model):
    _name = b'sped.ibptax.servico'
    _description = 'IBPTax por Serviço'

    ibptax_id = fields.Many2one(
        comodel_name='sped.ibptax',
        string='IBPTax',
        ondelete='cascade',
    )
    estado_id = fields.Many2one(
        comodel_name='sped.estado',
        string='Estado',
        related='ibptax_id.estado_id',
        store=True,
    )
    servico_id = fields.Many2one(
        comodel_name='sped.servico',
        string='Serviço',
    )
    al_ibpt_nacional = fields.Monetary(
        string='Nacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_internacional = fields.Monetary(
        string='Internacional',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
    al_ibpt_municipal = fields.Monetary(
        string='Municipal',
        digits=(5, 2),
        currency_field='currency_aliquota_id',
    )
