# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_returns(self):
        return super(
            StockReturnPicking,
            self.with_context(
                mail_create_nolog=True,
                tracking_disable=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
            ),
        )._create_returns()
