# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from psycopg2.extensions import AsIs
from odoo import api, fields, models, _


class SpedProduto(models.Model):
    _inherit = 'sped.produto'

    estoque_em_maos = fields.Monetary(
        string='Estoque em mãos',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_disponivel = fields.Monetary(
        string='Estoque disponível',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_previsto_entrada = fields.Monetary(
        string='Estoque previsto (entradas)',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_comprometido_saida = fields.Monetary(
        string='Estoque comprometido (saídas)',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_minimo = fields.Monetary(
        string='Estoque mínimo',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )
    estoque_maximo = fields.Monetary(
        string='Estoque máximo',
        currency_field='currency_unidade_id',
        compute='_compute_estoque',
    )

    def _compute_estoque(self):
        #
        # Como temos necessidade de cancelar e manter no sistema movimentos
        # de estoque que haviam sido anteriormente confirmados, os quants
        # não se atualizam automaticamente; de mais a mais, a quantidade
        # em estoque, para efeito de auditoria, por exigência dos clientes,
        # deve vir *somente* dos moves
        #
        sql_locais_saida = '''
        select distinct
            "stock_move".location_id
        from
            {sql_from}
        where
            "stock_move".state = 'done' and
            {sql_where};
        '''
        sql_locais_entrada = '''
        select distinct
            "stock_move".location_dest_id
        from
            {sql_from}
        where
            "stock_move".state = 'done' and
            {sql_where};
        '''

        sql_soma_move = '''
        select
            sum(smes.quantidade) as estoque_em_maos
        from
            stock_move_entrada_saida smes
        where
            smes.produto_id = %(produto_id)s
            and smes.location_id in %(local_ids)s;
        '''
        move = self.env['stock.move']

        for produto in self:
            local_ids = []

            domain_quant_loc, domain_move_in_loc, domain_move_out_loc = \
                produto.product_id._get_domain_locations()

            #
            # Buscamos quais locais devem ser analisados
            #
            sql_from, sql_where, sql_where_params = \
                move._where_calc(domain_move_in_loc).get_sql()

            sql = sql_locais_entrada.format(
                sql_from=sql_from, sql_where=sql_where)
            self.env.cr.execute(sql, sql_where_params)
            for local_id, in self.env.cr.fetchall():
                if local_id not in local_ids:
                    local_ids.append(local_id)

            sql_from, sql_where, sql_where_params = \
                move._where_calc(domain_move_out_loc).get_sql()

            sql = sql_locais_saida.format(
                sql_from=sql_from, sql_where=sql_where)
            self.env.cr.execute(sql, sql_where_params)
            for local_id, in self.env.cr.fetchall():
                if local_id not in local_ids:
                    local_ids.append(local_id)

            #
            # Agora, trazemos a quantidade apurada
            #
            if len(local_ids) > 0:
                self.env.cr.execute(sql_soma_move,
                    {'produto_id': produto.id,
                    'local_ids': AsIs(str(tuple(local_ids)).replace(',)', ')'))
                    })

                produto.estoque_em_maos = \
                    self.env.cr.dictfetchall()[0]['estoque_em_maos']
            else:
                produto.estoque_em_maos = 0

            produto.estoque_disponivel = produto.estoque_em_maos + \
                produto.incoming_qty - produto.outgoing_qty
            produto.estoque_previsto_entrada = produto.incoming_qty
            produto.estoque_comprometido_saida = produto.outgoing_qty
            produto.estoque_minimo = produto.reordering_min_qty
            produto.estoque_maximo = produto.reordering_max_qty
