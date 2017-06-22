# -*- coding: utf-8 -*-
#
# Copyright 2016 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.l10n_br_base.constante_tributaria import (
    AMBIENTE_NFE,
    INDICADOR_IE_DESTINATARIO_CONTRIBUINTE,
    REGIME_TRIBUTARIO_LUCRO_PRESUMIDO,
    REGIME_TRIBUTARIO_LUCRO_REAL,
    REGIME_TRIBUTARIO_SIMPLES,
    REGIME_TRIBUTARIO_SIMPLES_EXCESSO,
    TIPO_EMISSAO_NFE,
)

import logging

_logger = logging.getLogger(__name__)

try:
    from pybrasil.inscricao import (
        formata_cnpj, formata_cpf, limpa_formatacao,
        formata_inscricao_estadual, valida_cnpj, valida_cpf,
        valida_inscricao_estadual
    )
    from pybrasil.telefone import (
        formata_fone, valida_fone_fixo, valida_fone_celular,
        valida_fone_internacional
    )

except (ImportError, IOError) as err:
   _logger.debug(err)


class SpedEmpresa(models.Model):
    _inherit = 'sped.empresa'

    protocolo_id = fields.Many2one(
        comodel_name='sped.protocolo.icms',
        string='Protocolo padrão',
        ondelete='restrict',
        domain=[('tipo', '=', 'P')],
    )
    simples_anexo_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.anexo',
        string='Anexo do SIMPLES (produtos)',
        ondelete='restrict',
    )
    simples_teto_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.teto',
        string='Teto do SIMPLES',
        ondelete='restrict',
    )
    simples_aliquota_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.aliquota',
        string='Alíquotas do SIMPLES',
        ondelete='restrict',
        compute='_compute_simples_aliquota_id',
    )
    simples_anexo_servico_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.anexo',
        string='Anexo do SIMPLES (serviços)',
        ondelete='restrict',
    )
    simples_aliquota_servico_id = fields.Many2one(
        comodel_name='sped.aliquota.simples.aliquota',
        string='Alíquotas do SIMPLES (serviços)',
        ondelete='restrict',
        compute='_compute_simples_aliquota_id',
    )
    al_pis_cofins_id = fields.Many2one(
        comodel_name='sped.aliquota.pis.cofins',
        string='Alíquota padrão do PIS-COFINS',
        ondelete='restrict',
    )
    operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação padrão para venda',
        ondelete='restrict',
        domain=[('modelo', 'in', ('55', '65', '2D')), ('emissao', '=', '0')],
    )
    operacao_produto_pessoa_fisica_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação padrão para venda pessoa física',
        ondelete='restrict',
        domain=[('modelo', 'in', ('55', '65', '2D')), ('emissao', '=', '0')],
    )
    operacao_produto_ids = fields.Many2many(
        'sped.operacao',
        'res_partner_sped_operacao_produto',
        'partner_id',
        'operacao_id',
        string='Operações permitidas para venda',
        domain=[('modelo', 'in', ('55', '65', '2D')), ('emissao', '=', '0')],
    )
    operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao',
        string='Operação padrão para venda',
        ondelete='restrict',
        domain=[('modelo', 'in', ('SE', 'RL')), ('emissao', '=', '0')],
    )
    operacao_servico_ids = fields.Many2many(
        'sped.operacao',
        'res_partner_sped_operacao_servico',
        'partner_id',
        'operacao_id',
        string='Operações permitidas para venda',
        domain=[('modelo', 'in', ('SE', 'RL')), ('emissao', '=', '0')],
    )
    #
    # Emissão de NF-e, NFC-e e NFS-e
    #
    ambiente_nfe = fields.Selection(
        selection=AMBIENTE_NFE,
        string='Ambiente NF-e',
    )
    tipo_emissao_nfe = fields.Selection(
        selection=TIPO_EMISSAO_NFE,
        string='Tipo de emissão NF-e'
    )
    serie_nfe_producao = fields.Char(
        string='Série em produção',
        size=3,
        default='1'
    )
    serie_nfe_homologacao = fields.Char(
        string='Série em homologação',
        size=3,
        default='100'
    )
    serie_nfe_contingencia_producao = fields.Char(
        string='Série em produção',
        size=3,
        default='900'
    )
    serie_nfe_contingencia_homologacao = fields.Char(
        string='Série em homologação',
        size=3,
        default='999'
    )
    ambiente_nfce = fields.Selection(
        selection=AMBIENTE_NFE,
        string='Ambiente NFC-e'
    )
    tipo_emissao_nfce = fields.Selection(
        selection=TIPO_EMISSAO_NFE,
        string='Tipo de emissão NFC-e'
    )
    serie_nfce_producao = fields.Char(
        selection='Série em produção',
        size=3,
        default='1'
    )
    serie_nfce_homologacao = fields.Char(
        string='Série em homologação',
        size=3,
        default='100'
    )
    serie_nfce_contingencia_producao = fields.Char(
        string='Série em homologação',
        size=3,
        default='900'
    )
    serie_nfce_contingencia_homologacao = fields.Char(
        string='Série em produção',
        size=3,
        default='999'
    )
    csc_id = fields.Integer(
        string='ID CSC',
        default=1,
    )
    csc_codigo = fields.Char(
        string='Código CSC',
        size=36,
    )
    ambiente_nfse = fields.Selection(
        selection=AMBIENTE_NFE,
        string='Ambiente NFS-e'
    )
    # provedor_nfse = fields.Selection(PROVEDOR_NFSE, 'Provedor NFS-e')
    serie_rps_producao = fields.Char(
        string='Série em produção',
        size=3,
        default='1'
    )
    serie_rps_homologacao = fields.Char(
        string='Série em produção',
        size=3,
        default='100'
    )
    ultimo_rps = fields.Integer(
        string='Último RPS'
    )
    ultimo_lote_rps = fields.Integer(
        string='Último lote de RPS'
    )

    @api.depends('simples_anexo_id', 'simples_anexo_servico_id',
                 'simples_teto_id')
    def _compute_simples_aliquota_id(self):
        for empresa in self:
            simples_aliquota_ids = self.env[
                'sped.aliquota.simples.aliquota'].search([
                    ('anexo_id', '=', empresa.simples_anexo_id.id),
                    ('teto_id', '=', empresa.simples_teto_id.id),
                ])

            if len(simples_aliquota_ids) != 0:
                empresa.simples_aliquota_id = simples_aliquota_ids[0]
            else:
                empresa.simples_aliquota_id = False

            simples_aliquota_ids = self.env[
                'sped.aliquota.simples.aliquota'].search([
                    ('anexo_id', '=', empresa.simples_anexo_servico_id.id),
                    ('teto_id', '=', empresa.simples_teto_id.id),
                ])

            if len(simples_aliquota_ids) != 0:
                empresa.simples_aliquota_servico_id = simples_aliquota_ids[0]
            else:
                empresa.simples_aliquota_servico_id = False

    @api.onchange('regime_tributario')
    def onchange_regime_tributario(self):
        valores = {}
        res = {'value': valores}

        if self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES:
            valores.update(al_pis_cofins_id=self.env.ref(
                'sped_imposto.ALIQUOTA_PIS_COFINS_SIMPLES').id)

        elif self.regime_tributario == REGIME_TRIBUTARIO_SIMPLES_EXCESSO:
            valores.update(al_pis_cofins_id=self.env.ref(
                'sped_imposto.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id)

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_PRESUMIDO:
            valores.update(al_pis_cofins_id=self.env.ref(
                'sped_imposto.ALIQUOTA_PIS_COFINS_LUCRO_PRESUMIDO').id)

        elif self.regime_tributario == REGIME_TRIBUTARIO_LUCRO_REAL:
            valores.update(al_pis_cofins_id=self.env.ref(
                'sped_imposto.ALIQUOTA_PIS_COFINS_LUCRO_REAL').id)

        return res
