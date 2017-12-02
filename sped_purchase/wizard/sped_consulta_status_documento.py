# -*- coding: utf-8 -*-
# Copyright (C) 2013 Luis Felipe Miléo - KMEE
# Copyright (C) 2014 Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from __future__ import division, print_function, unicode_literals

from odoo.addons.l10n_br_base.constante_tributaria import (
    AMBIENTE_NFE,
    SITUACAO_NFE,
)
from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError


class SpedConsultaStatusDocumento(models.TransientModel):
    """Consulta status de documento fiscal"""
    _name = b'sped_purchase.consulta_status_documento'
    _description = 'Consulta Status Documento'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
        required=True,
        default=lambda self: self.env.user.sped_empresa_id,
    )
    state = fields.Selection(
        selection=[('init', 'Init'),
                   ('error', 'Error'),
                   ('done', 'Done')],
        string='State',
        select=True,
        readonly=True,
        default='init')
    versao = fields.Text(
        string=u'Versão', readonly=True)
    ambiente_nfe = fields.Selection(
        selection=AMBIENTE_NFE,
        string='Ambiente da NF-e',
    )
    motivo = fields.Text(
        string='Motivo',
        readonly=True)
    codigo_uf = fields.Integer(
        string='Codigo Estado',
        readonly=True
    )
    chave = fields.Char(
        string='Chave',
        size=44,
    )
    protocolo_autorizacao = fields.Char(
        string='Protocolo de autorização',
        readonly=True,
        size=60,
    )
    protocolo_cancelamento = fields.Char(
        string='Protocolo de cancelamento',
        readonly=True,
        size=60,
    )
    situacao_nfe = fields.Selection(
        string=u'Situacação da NF-e',
        selection=SITUACAO_NFE,
        select=True,
        readonly=True,
    )
    processamento_evento_nfe = fields.Text(
        sting='Processamento Evento NFE',
        readonly=True,
    )

    @api.multi
    def busca_status_documento(self):
        self.ensure_one()
        try:
            processador = self.empresa_id.processador_nfe()
            processo = processador.consultar_nota(
                processador.ambiente,
                chave_nfe=self.chave,
                nfe=False
            )
            dados = {
                'versao': processo.resposta.versao.valor,
                'motivo': processo.resposta.cStat.txt + ' - ' +
                           processo.resposta.xMotivo.txt,
                'codigo_uf': processo.resposta.cUF.txt,
                'chave': processo.resposta.chNFe.txt,
                'ambiente_nfe': processo.resposta.tpAmb.txt,
                'protocolo_autorizacao':
                    '' if processo.resposta.protNFe is None else
                    processo.resposta.protNFe.infProt.nProt.txt,
                'protocolo_cancelamento': '',
                'processamento_evento_nfe': '',
                'state': 'done',
            }
            self.write(dados)
        except Exception as e:
            raise UserError(
                _(u'Erro na consulta da chave!'), e)

        result = self.env.ref(
            'sped_purchase.action_sped_consulta_status_documento'
        ).read()[0]
        result['res_id'] = self.id
        return result
