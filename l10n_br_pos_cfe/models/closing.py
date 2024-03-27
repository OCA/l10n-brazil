# © 2023 KMEE INFORMATICA LTDA (https://kmee.com.br)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import logging
import os

from odoo import _, fields, models
from odoo.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)

try:
    from erpbrasil.base import misc
except ImportError:
    _logger.error("Biblioteca erpbrasil.base não instalada")


class FiscalClosing(models.Model):
    _inherit = "l10n_br_fiscal.closing"

    document_cfe_pos_ids = fields.One2many(
        comodel_name="pos.order",
        string="CFe POS Documents",
        inverse_name="close_id",
    )

    def _prepare_files(self, temp_dir):
        temp_dir = super(FiscalClosing, self)._prepare_files(temp_dir)
        date_min, date_max = self._date_range()
        orders = self.env["pos.order"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("date_order", ">=", date_min),
                ("date_order", "<=", date_max),
                ("state", "not in", ["draft"]),
                ("amount_paid", ">=", 0),
                ("authorization_file", "!=", False),
            ]
        )

        document_path = "/".join(
            [misc.punctuation_rm(self.company_id.cnpj_cpf), "cfe_pos"]
        )

        for order in orders:
            try:
                filename = os.path.join(
                    temp_dir, document_path, f"{order.document_key}.xml"
                )
                if not os.path.exists(os.path.dirname(filename)):
                    os.makedirs(os.path.dirname(filename))

                with open(filename, "wb") as file:
                    file.write(base64.b64decode(order.authorization_file))

                if order.cancel_document_key:
                    filename = os.path.join(
                        temp_dir, document_path, f"{order.cancel_document_key}.xml"
                    )
                    if not os.path.exists(os.path.dirname(filename)):
                        os.makedirs(os.path.dirname(filename))

                    with open(filename, "wb") as file:
                        file.write(base64.b64decode(order.cancel_file))
            except OSError as e:
                raise RedirectWarning(_("Error!"), _("I/O Error")) from e
            except PermissionError as e:
                raise RedirectWarning(
                    _("Error!"), _("Check write permissions in your system temp folder")
                ) from e
            except Exception:
                _logger.error(
                    _(
                        "Replication failed: document attachments "
                        "[id = {}] is not present in the database."
                    ).format(order.name)
                )

        self.write({"document_cfe_pos_ids": [(6, 0, orders.ids)]})

        return temp_dir
