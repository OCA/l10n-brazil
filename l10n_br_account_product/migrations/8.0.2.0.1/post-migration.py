# -*- coding: utf-8 -*-
# @ 2016 Akretion - www.akretion.com.br -
#   Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.openupgrade import openupgrade


@openupgrade.migrate()
def migrate(cr, version):

    openupgrade.logged_query(
        cr,
        """UPDATE product_template SET fiscal_classification_id = ncm_id;
        """)
    openupgrade.logged_query(
        cr,
        """UPDATE account_product_fiscal_classification SET code = name;
        """)
    openupgrade.logged_query(
        cr,
        """UPDATE account_product_fiscal_classification SET name = description;
        """)
