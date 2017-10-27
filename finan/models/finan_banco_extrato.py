# -*- coding: utf-8 -*-
#
# Copyright 2017 Taŭga Tecnologia
#   Aristides Caldeira <aristides.caldeira@tauga.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.addons.l10n_br_base.models.sped_base import SpedBase
from ..constantes import *


SQL_FINAN_BANCO_EXTRATO_FUNCTION = '''
drop function if exists finan_banco_extrato_function(integer);
create or replace function finan_banco_extrato_function(_banco_id integer)
    returns table(
        ordem integer,
        lancamento_id integer,
        data date,
        entrada numeric,
        saida numeric,
        saldo numeric
    ) as
    $BODY$
        declare
            valor numeric := 0;
            ultima_data date := '2000-01-01';

        begin
            ordem := 0;
            saldo := 0;

            --
            -- Primeiro, trazemos o extrato que já está salvo
            --
            for
                ordem,
                lancamento_id,
                data,
                entrada,
                saida,
                saldo

            in
            select
                fbe.ordem,
                fbe.lancamento_id,
                fbe.data,
                fbe.entrada,
                fbe.saida,
                fbe.saldo

            from
                finan_banco_extrato fbe

            where
                fbe.banco_id = _banco_id

            order by
                fbe.ordem

            loop
                ultima_data := data;
                return next;
            end loop;

            --
            -- Agora recalculamos da última data em diante
            --
            for
                lancamento_id,
                data,
                entrada,
                saida,
                valor

            in
            select
                fl.id as lancamento_id,
                fl.data_extrato as data,
                case
                    when fl.sinal = 1 then coalesce(fl.vr_total, 0)
                    else 0
                end as entrada,
                case
                    when fl.sinal = -1 then coalesce(fl.vr_total, 0)
                    else 0
                end as saida,
                cast(coalesce(fl.vr_total, 0)
                    * coalesce(fl.sinal, 1) as numeric(18, 2)) as valor

            from
                finan_lancamento fl

            where
                fl.banco_id = _banco_id
                and fl.tipo in ('recebimento', 'pagamento', 'entrada', 'saida')
                and (fl.provisorio is null or fl.provisorio = False)
                and fl.data_extrato > ultima_data

            order by
                fl.data_extrato,
                coalesce(fl.vr_total, 0) * coalesce(fl.sinal, 1) desc

            loop
                saldo := coalesce(saldo, 0) + valor;
                ordem := coalesce(ordem, 0) + 1;
                return next;
            end loop;
        end
    $BODY$
LANGUAGE plpgsql VOLATILE;
'''

SQL_INDICES = '''
create index if not exists finan_banco_extrato_banco_id_ordem_index
    on finan_banco_extrato (banco_id, ordem);

create index if not exists finan_banco_extrato_banco_id_data_index
    on finan_banco_extrato (banco_id, data);
'''

class FinanBancoExtrato(SpedBase, models.Model):
    _name = b'finan.banco.extrato'
    _description = 'Extratos de Contas Bancárias'
    #_rec_name = 'nome'
    _order = 'banco_id, ordem'

    banco_id = fields.Many2one(
        comodel_name='finan.banco',
        string='Banco/caixa',
        index=True,
        ondelete='restrict',
    )
    ordem = fields.Integer(
        string='Ordem',
        index=True,
    )
    lancamento_id = fields.Many2one(
        comodel_name='finan.lancamento',
        string='Lançamento',
        index=True,
    )
    data = fields.Date(
        string='Data',
        index=True,
    )
    entrada = fields.Monetary(
        string='Entrada',
    )
    saida = fields.Monetary(
        string='Saída',
    )
    saldo = fields.Monetary(
        string='Saldo',
    )

    @api.model_cr
    def init(self):
        self.env.cr.execute(SQL_FINAN_BANCO_EXTRATO_FUNCTION)
        self.env.cr.execute(SQL_INDICES)

    def ajusta_extrato(self, banco_id, data):
        sql = '''
        delete from finan_banco_extrato fbe
        where
            fbe.banco_id = %(banco_id)s
            and fbe.data >= %(data)s;

        insert into finan_banco_extrato (
            banco_id,
            ordem,
            lancamento_id,
            data,
            entrada,
            saida,
            saldo
        )
        select
            %(banco_id)s as banco_id,
            fbef.ordem,
            fbef.lancamento_id,
            fbef.data,
            fbef.entrada,
            fbef.saida,
            fbef.saldo
        from
            finan_banco_extrato_function(%(banco_id)s) fbef
        where
            fbef.data >= %(data)s;
        '''
        filtros = {
            'banco_id': banco_id,
            'data': data,
        }
        self.env.cr.execute(sql, filtros)
