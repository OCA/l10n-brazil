# © 2022 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_post_with_view(self, views_or_xmlid, **kwargs):
        try:
            pos_order = self.env["pos.order"].search(
                [("name", "=", kwargs["values"]["origin"].origin)]
            )
            if not pos_order:
                return super().message_post_with_view(views_or_xmlid, **kwargs)
        except Exception:
            return super().message_post_with_view(views_or_xmlid, **kwargs)
