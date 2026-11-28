# © 2016 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_post_with_source(self, source_ref, render_values=None, **kwargs):
        try:
            pos_order = self.env["pos.order"].search(
                [("name", "=", render_values["origin"].origin)]
            )
            if not pos_order:
                return super().message_post_with_source(
                    source_ref, render_values=render_values, **kwargs
                )
        except Exception:
            return super().message_post_with_source(
                source_ref, render_values=render_values, **kwargs
            )
