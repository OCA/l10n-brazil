# -*- coding: utf-8 -*-
# Copyright (C) 2015  Renato Lima - www.akretion.com.br
# Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp.openupgrade import openupgrade


@openupgrade.migrate()
def migrate(cr, version):

    cr.execute(
        """
        UPDATE ir_model_data
         SET name = 'fc_00255d8d158663217906abb312aa0759'
          WHERE name = 'fiscal_category_venda_servico'
        """)
