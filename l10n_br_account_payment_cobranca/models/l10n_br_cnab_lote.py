# -*- coding: utf-8 -*-
# © 2012 KMEE INFORMATICA LTDA
#   @author  Luiz Felipe do Divino Costa <luiz.divino@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models, fields
from .l10n_br_cnab import STATE
_logger = logging.getLogger(__name__)


class L10nBrCnabLote(models.Model):

    _name = "l10n_br.cnab.lote"

    account_bank_id = fields.Many2one(
        string=u"Conta Bancária",
        comodel_name="res.partner.bank",
    )
    cnab_id = fields.Many2one(
        string="CNAB",
        comodel_name="l10n_br.cnab",
        ondelete='cascade',
    )
    empresa_inscricao_numero = fields.Char(
        string=u"Número de Inscrição"
    )
    empresa_inscricao_tipo = fields.Char(
        string=u"Tipo de Inscrição"
    )
    evento_id = fields.One2many(
        string="Eventos",
        comodel_name="l10n_br.cnab.evento",
        inverse_name="lote_id",
    )
    mensagem = fields.Char(
        string="Mensagem"
    )
    qtd_registros = fields.Integer(
        string="Quantidade de Registros"
    )
    servico_operacao = fields.Char(
        string=u"Tipo de Operação"
    )
    state = fields.Selection(
        string="State",
        related="cnab_id.state",
        selection=STATE,
        default="draft",
    )
    tipo_servico = fields.Char(
        string=u"Tipo do Serviço"
    )
    total_valores = fields.Float(
        string="Valor Total"
    )
