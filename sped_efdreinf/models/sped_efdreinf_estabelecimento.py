# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SpedEfdReinfEstab(models.Model):
    _name = 'sped.efdreinf.estabelecimento'
    _description = 'Prestadores de Eventos Periódicos EFD/Reinf'
    _rec_name = 'nome'
    _order = "nome"

    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    efdreinf_id = fields.Many2one(
        string='EFD/Reinf',
        comodel_name='sped.efdreinf',
    )
    estabelecimento_id = fields.Many2one(
        string='Estabelecimento',
        comodel_name='res.company',
    )
    prestador_id = fields.Many2one(
        string='Prestador',
        comodel_name='res.partner',
    )
    vr_total_bruto = fields.Float(
        string='Valor Total Bruto',
        digits=[14, 2],
    )
    vr_total_base_retencao = fields.Float(
        string='Base de Retenção',
        digits=[14, 2],
    )
    vr_total_ret_princ = fields.Float(
        string='Total de Retenções',
        digits=[14, 2],
    )
    vr_total_ret_adic = fields.Float(
        string='Adicionais de Retenção das NFs',
        digits=[14, 2],
    )
    vr_total_nret_princ = fields.Float(
        string='Total Não Retido devido a Ações',
        digits=[14, 2],
    )
    vr_total_nret_adic = fields.Float(
        string='Total Retido Adicional devido a Ações',
        digits=[14, 2],
    )
    ind_cprb = fields.Binary(
        string='Prestador é CPRB ?',
    )
    nfs_ids = fields.One2many(
        string='Notas Fiscais',
        comodel_name='sped.efdreinf.nfs',
        inverse_name='estabelecimento_id',
    )
    sped_R2010 = fields.Boolean(
        string='Ativação EFD/Reinf',
        compute='_compute_sped_R2010',
    )
    sped_R2010_registro = fields.Many2one(
        string='Registro R-2010',
        comodel_name='sped.transmissao',
    )
    situacao_R2010 = fields.Selection(
        string='Situação R-2010',
        selection=[
            ('1', 'Pendente'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        related='sped_R2010_registro.situacao',
        readonly=True,
    )

    @api.depends('estabelecimento_id', 'prestador_id')
    def _compute_nome(self):
        for prestador in self:
            nome = prestador.estabelecimento_id.name
            if prestador.prestador_id and prestador.prestador_id != prestador.estabelecimento_id:
                nome += '/' + prestador.prestador_id.name

            prestador.nome = nome

    @api.depends('sped_R2010_registro')
    def _compute_sped_R2010(self):
        for efdreinf in self:
            efdreinf.sped_R2010 = True if efdreinf.sped_R2010_registro else False

