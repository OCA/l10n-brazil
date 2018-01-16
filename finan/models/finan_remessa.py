# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *

from pybrasil.febraban import *
from odoo.exceptions import UserError


class FinanRemessa(SpedBase, models.Model):
    _name = b'finan.remessa'
    _description = 'Remessa Bancária'
    _rec_name = 'numero'
    _order = 'data desc'

    carteira_id = fields.Many2one(
        comodel_name='finan.carteira',
        string='Carteira',
        required=True,
        index=True,
    )
    numero = fields.Integer(
        string='Número',
    )
    data = fields.Datetime(
        string='Data',
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    lancamento_ids = fields.Many2many(
        comodel_name='finan.lancamento',
        relation='finan_remessa_lancamento',
        column1='remessa_id',
        column2='lancamento_id',
        string='Lançamentos',
    )

    def gera_arquivo(self):
        self.ensure_one()

        #
        # Pegamos a carteira com o usuário admin, assim podemos ajustar o nº
        # da próxima remessa sem problemas de permissão pro operador
        # financeiro; em geral, somente o gerente poderia ajustar o nº da
        # próxima remessa na carteira
        #
        carteira = \
            self.env['finan.carteira'].sudo().browse(self.carteira_id.id)

        if not self.numero:
            self.numero = carteira.proxima_remessa
            carteira.proxima_remessa += 1

        boletos = []
        for lancamento in self.lancamento_ids:
            boleto = lancamento.gera_boleto(sem_anexo=True)
            boletos.append(boleto)

        if boletos:
            remessa = RemessaBoleto()
            #remessa.tipo = 'CNAB_400'
            #remessa.tipo = 'CNAB_240'
            remessa.boletos = boletos
            remessa.sequencia = self.numero
            remessa.data_hora = self.data + ' UTC'

            self._grava_anexo(
                nome_arquivo=remessa.nome_arquivo,
                conteudo=remessa.arquivo_remessa
            )
        else:
            raise UserError('É preciso adicionar boletos para gerar um arquivo.')
