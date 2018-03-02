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
from lxml import objectify
import re
import base64


class SpedConsultaStatusDocumento(models.TransientModel):
    """Consulta status de documento fiscal"""
    _name = b'sped_purchase.consulta_status_documento'
    _description = 'Consulta Status Documento'

    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
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
        size=60,
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
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Pedido de Compra',
        copy=False,
    )

    arquivo = fields.Binary(
        string='Arquivo',
        attachment=True,
    )

    forma_consulta = fields.Selection(
        selection=[
            ('Chave', 'Chave'),
            ('XML', 'XML'),
        ],
        string="Forma de Consulta",
        required=True,
        default='Chave',
        help="Seleciona se a consulta será feita pela chave da NF-e ou pelo "
             "XML da NF-e"
    )

    @api.model
    def create(self, vals):

        if vals.get('chave'):
            chave = ''.join(re.findall(r'[\b]*\d+[\b]*', vals.get('chave')))
            vals.update(chave=chave)

        res = super(SpedConsultaStatusDocumento, self).create(vals)
        return res

    @api.multi
    def busca_status_documento(self):
        self.ensure_one()

        if self.forma_consulta == 'XML':
            xml = base64.b64decode(self.arquivo)

            nfe = objectify.fromstring(xml)

            if('procEventoNFe' in nfe.tag):
                if(nfe.evento.infEvento.detEvento.
                        descEvento == 'Cancelamento'):

                    documentos = self.env['sped.documento'].\
                        importa_nfe_cancelada(xml)

                    if documentos:
                        return {
                            'name': _("NF-e Cancelada"),
                            'view_mode': 'form',
                            'view_type': 'form',
                            'view_id': self.env.ref(
                                'sped_nfe.sped_documento_ajuste_recebimento_form').id,
                            'res_id': documentos[0].id,
                            'res_model': 'sped.documento',
                            'type': 'ir.actions.act_window',
                            'target': 'current',
                            'flags': {'form': {'action_buttons': True}},
                        }

            documento = self.env['sped.documento'].new()
            documento.modelo = nfe.NFe.infNFe.ide.mod.text
            dados = documento.le_nfe(xml=xml)
            return {
                'name': _("Associar Pedido de Compras"),
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': self.env.ref(
                    'sped_nfe.sped_documento_ajuste_recebimento_form').id,
                'res_id': dados.id,
                'res_model': 'sped.documento',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': {'default_purchase_order_ids': [
                    (4, self.purchase_order_id.id)]},
                'flags': {'form': {'action_buttons': True,
                                   'options': {'mode': 'edit'}}},
            }

        consulta = self.env['sped.consulta.dfe']
        consulta.validate_nfe_configuration(self.empresa_id)

        try:

            nfe_result = consulta.download_nfe(self.empresa_id, self.chave)

            if nfe_result['code'] == '138':
                nfe = objectify.fromstring(nfe_result['nfe'])
                documento = self.env['sped.documento'].new()
                documento.modelo = nfe.NFe.infNFe.ide.mod.text
                dados = documento.le_nfe(xml=nfe_result['nfe'])
                return {
                    'name': _("Associar Pedido de Compras"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'view_id': self.env.ref(
                        'sped_nfe.sped_documento_ajuste_recebimento_form').id,
                    'res_id': dados.id,
                    'res_model': 'sped.documento',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': {'default_purchase_order_ids': [
                        (4, self.purchase_order_id.id)]},
                    'flags': {'form': {'action_buttons': True,
                                       'options': {'mode': 'edit'}}},
                }

        except Exception as e:
            raise UserError(
                _(u'Erro na consulta da chave!', e))
