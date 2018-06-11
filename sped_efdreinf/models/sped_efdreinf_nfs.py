# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from datetime import datetime


class SpedEfdReinfNFS(models.Model):
    _name = 'sped.efdreinf.nfs'
    _description = 'NFs de Eventos Periódicos EFD/Reinf'
    _rec_name = 'nome'
    _order = "nome"

    estabelecimento_id = fields.Many2one(
        string='Prestador',
        comodel_name='sped.efdreinf.estabelecimento',
    )
    nome = fields.Char(
        string='Nome',
        compute='_compute_nome',
        store=True,
    )
    nfs_id = fields.Many2one(
        string='NF',
        comodel_name='account.invoice',
    )
    serie = fields.Char(
        string='Série',
        related='nfs_id.serie_nfe',
        readonly=True,
        store=True,
    )
    num_docto = fields.Char(
        string='NF #',
        related='nfs_id.internal_number',
        readonly=True,
        store=True,
    )
    dt_emissao_nf = fields.Datetime(
        string='Emitido em',
        related='nfs_id.date_hour_invoice',
        readonly=True,
        store=True,
    )
    vr_bruto = fields.Float(
        string='Valor Bruto',
        related='nfs_id.amount_total',
        readonly=True,
        store=True,
    )
    observacoes = fields.Char(
        string='Observações',
        size=250,
    )
    servico_ids = fields.One2many(
        string='Serviços',
        comodel_name='sped.efdreinf.servico',
        inverse_name='efdreinf_nfs_id',
    )

    @api.depends('num_docto', 'vr_bruto', 'dt_emissao_nf')
    def _compute_nome(self):
        for nfs in self:
            nome = nfs.num_docto or ''
            if nfs.dt_emissao_nf:
                data = fields.Datetime.from_string(nfs.dt_emissao_nf)
                data = datetime.strftime(data, '%d/%m/%Y - %H:%M:%S')
                valor = nfs.vr_bruto or 0
                nome += ' (' + data + ')'
            nome += ' R$ ' + '{:20,.2f}'.format(valor)
