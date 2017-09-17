# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.tools.sql import drop_view_if_exists


SQL_FINAN_CONTA_ARVORE_VIEW = '''
create or replace view finan_conta_arvore_view as
select
    a1.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    1 as nivel
from
    finan_conta a1

union all

select
    a2.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    2 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id

union all

select
    a3.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    3 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id

union all

select
    a4.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    4 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id

union all

select
    a5.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    5 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id

union all

select
    a6.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    6 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id
    join finan_conta a6 on a5.conta_superior_id = a6.id

union all

select
    a7.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    7 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id
    join finan_conta a6 on a5.conta_superior_id = a6.id
    join finan_conta a7 on a6.conta_superior_id = a7.id

union all

select
    a8.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    8 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id
    join finan_conta a6 on a5.conta_superior_id = a6.id
    join finan_conta a7 on a6.conta_superior_id = a7.id
    join finan_conta a8 on a7.conta_superior_id = a8.id

union all

select
    a9.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    9 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id
    join finan_conta a6 on a5.conta_superior_id = a6.id
    join finan_conta a7 on a6.conta_superior_id = a7.id
    join finan_conta a8 on a7.conta_superior_id = a8.id
    join finan_conta a9 on a8.conta_superior_id = a9.id

union all

select
    a10.id as conta_superior_id,
    a1.id as conta_relacionada_id,
    10 as nivel
from
    finan_conta a1
    join finan_conta a2 on a1.conta_superior_id = a2.id
    join finan_conta a3 on a2.conta_superior_id = a3.id
    join finan_conta a4 on a3.conta_superior_id = a4.id
    join finan_conta a5 on a4.conta_superior_id = a5.id
    join finan_conta a6 on a5.conta_superior_id = a6.id
    join finan_conta a7 on a6.conta_superior_id = a7.id
    join finan_conta a8 on a7.conta_superior_id = a8.id
    join finan_conta a9 on a8.conta_superior_id = a9.id
    join finan_conta a10 on a9.conta_superior_id = a10.id;
'''

DROP_TABLE = '''
    DROP TABLE IF EXISTS finan_conta_arvore
'''

SQL_SELECT_FINAN_CONTA_ARVORE = '''
select
  row_number() over() as id,
  conta_relacionada_id,
  conta_superior_id,
  nivel

from
  finan_conta_arvore_view

order by
  conta_relacionada_id,
  conta_superior_id;
'''

SQL_FINAN_CONTA_ARVORE_TABLE = '''
create table finan_conta_arvore as
''' + SQL_SELECT_FINAN_CONTA_ARVORE + '''

create index finan_conta_arvore_conta_relacionada_id
  on finan_conta_arvore
  (conta_relacionada_id);

create index finan_conta_arvore_conta_superior_id
  on finan_conta_arvore
  (conta_superior_id);

create index finan_conta_arvore_nivel
  on finan_conta_arvore
  (nivel);
'''


class FinanContaArvore(models.Model):
    _name = b'finan.conta.arvore'
    _description = 'Conta Financeira - Árvore de Análise'
    _auto = False

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'finan_conta_arvore_view')
        self._cr.execute(DROP_TABLE)
        self._cr.execute(SQL_FINAN_CONTA_ARVORE_VIEW)
        self._cr.execute(SQL_FINAN_CONTA_ARVORE_TABLE)

    conta_superior_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta superior',
        index=True,
    )
    conta_relacionada_id = fields.Many2one(
        comodel_name='finan.conta',
        string='Conta relacionada',
        index=True,
    )
    nivel = fields.Integer(
        string='Nível',
        index=True,
    )
