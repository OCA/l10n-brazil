# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#    Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models, _


SQL_STOCK_MOVE_ENTRADA_SAIDA = '''
-- drop materialized view if exists stock_move_entrada_saida;
-- create materialized view stock_move_entrada_saida as

drop view if exists stock_move_entrada_saida;
create view stock_move_entrada_saida as

select
    m.id * -1 as id,
    m.id as move_id,
    coalesce(coalesce(sd.empresa_id, e.id), e.id) as empresa_id,
    m.sped_documento_id as documento_id,
    m.picking_id,
    m.location_id,
    m.produto_id,
    m.data,
    sdi.cfop_id,
    -1 as sinal,
    coalesce(m.quantidade, 0) * -1 as quantidade,
    0 as vr_unitario,
    0 as vr_produtos

from
    stock_move m
    left join sped_empresa e on e.company_id = m.company_id
    left join sped_documento sd on sd.id = m.sped_documento_id
    left join sped_documento_item sdi on sdi.id = m.sped_documento_item_id
    left join stock_picking p on p.id = m.picking_id

where
    m.state = 'done'

union all

select
    m.id as id,
    m.id as move_id,
    coalesce(coalesce(sd.empresa_id, p.empresa_id), e.id) as empresa_id,
    m.sped_documento_id as documento_id,
    m.picking_id,
    m.location_dest_id as location_id,
    m.produto_id,
    m.data,
    sdi.cfop_id,
    1 as sinal,
    coalesce(m.quantidade, 0) as quantidade,
    --
    -- O valor unitário da entrada vai determinar o custo médio posteriormente;
    -- tratar depois a questão do valor de inventário na implantação do sistema
    --
    case
        when c.custo_venda = True then sdi.vr_unitario_custo_comercial
        -- when inventario then inventario.vr_unitario
        else 0
    end as vr_unitario,
    case
        when c.custo_venda = True then sdi.vr_custo_comercial
        -- when inventario then inventario.vr_unitario
        else 0
    end as vr_produtos

from
    stock_move m
    left join sped_empresa e on e.company_id = m.company_id
    left join sped_documento sd on sd.id = m.sped_documento_id
    left join sped_documento_item sdi on sdi.id = m.sped_documento_item_id
    left join sped_cfop c on c.id = sdi.cfop_id and c.custo_venda = True
    left join stock_picking p on p.id = m.picking_id

where
    m.state = 'done';

-- create index stock_move_entrada_saida_sinal_index on stock_move_entrada_saida (sinal);
-- create index stock_move_entrada_saida_empresa_index on stock_move_entrada_saida (empresa_id);
-- create index stock_move_entrada_saida_documento_index on stock_move_entrada_saida (documento_id);
-- create index stock_move_entrada_saida_picking_index on stock_move_entrada_saida (picking_id);
-- create index stock_move_entrada_saida_location_index on stock_move_entrada_saida (location_id);
-- create index stock_move_entrada_saida_produto_index on stock_move_entrada_saida (produto_id);
-- create index stock_move_entrada_saida_cfop_index on stock_move_entrada_saida (cfop_id);
'''


class StockMoveCusto(models.Model):
    _name = b'stock.move.entrada.saida'
    _description = 'Movimento de Estoque - Entradas e Saídas'
    _auto = False
    _order = 'produto_id, data, sinal desc, quantidade desc'

    @api.model_cr
    def init(self):
        self._cr.execute(SQL_STOCK_MOVE_ENTRADA_SAIDA)

    move_id = fields.Many2one(
        comodel_name='stock.move',
        string='Movimento de Estoque',
    )
    empresa_id = fields.Many2one(
        comodel_name='sped.empresa',
        string='Empresa',
    )
    documento_id = fields.Many2one(
        comodel_name='sped.documento',
        string='Documento Fiscal',
    )
    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Ordem de Entrega',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Local de Estoque',
    )
    produto_id = fields.Many2one(
        comodel_name='sped.produto',
        string='Produto',
    )
    data = fields.Date(
        string='Data',
    )
    cfop_id = fields.Many2one(
        comodel_name='sped.cfop',
        string='CFOP',
    )
    cfop = fields.Char(
        string='CFOP',
    )
    sinal = fields.Integer(
        string='Sinal',
    )
    unidade_id = fields.Many2one(
        comodel_name='sped.unidade',
        string='Unidade',
        related='produto_id.unidade_id',
        readonly=True,
    )
    currency_unidade_id = fields.Many2one(
        comodel_name='res.currency',
        string='Unidade',
        related='unidade_id.currency_id',
        readonly=True,
    )
    quantidade = fields.Monetary(
        string='Quantidade',
        currency_field='currency_unidade_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        related='empresa_id.currency_id',
        readonly=True,
    )
    currency_unitario_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        related='empresa_id.currency_unitario_id',
        readonly=True,
    )
    vr_unitario = fields.Monetary(
        string='Valor unitário',
        currency_field='currency_unitario_id',
    )
    vr_produtos = fields.Monetary(
        string='Valor',
    )
