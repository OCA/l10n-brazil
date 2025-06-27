# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class StockInvoiceOnshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    vol_ids = fields.One2many(
        string="Volume Data",
        comodel_name="stock.invoice.onshipping.vol",
        inverse_name="invoice_wizard_id",
    )

    def _build_invoice_values_from_pickings(self, pickings):
        invoice, values = super()._build_invoice_values_from_pickings(pickings)

        # Volumes
        vol_ids = self.vol_ids.filtered(lambda v: v.picking_id in pickings)
        values["nfe40_vol"] = [
            (
                0,
                0,
                self._convert_volumes_to_write(vol_id),
            )
            for vol_id in vol_ids
        ]

        return invoice, values

    def _convert_volumes_to_write(self, data):
        """Prepare wizard lines for writing to fiscal document."""
        return {
            "nfe40_qVol": data.nfe40_qVol,
            "nfe40_esp": data.nfe40_esp,
            "nfe40_marca": data.nfe40_marca,
            "nfe40_pesoL": data.nfe40_pesoL,
            "nfe40_pesoB": data.nfe40_pesoB,
        }

    def _get_picking(self):
        picking_ids = self._load_pickings()
        if not picking_ids:
            raise UserError(_("No picking 2binvoiced!"))
        return picking_ids

    @api.model
    def default_get(self, fields_list):
        """
        Inherit to add default vol_ids
        :param fields_list: list of str
        :return: dict
        """
        result = super().default_get(fields_list)

        picking_ids = self._load_pickings()
        if not picking_ids:
            raise UserError(_("No picking 2binvoiced!"))

        vols_data = picking_ids.prepare_vols_data_from_picking()
        vol_ids = [Command.create(vol) for vol in vols_data]

        result["vol_ids"] = vol_ids
        return result

    def action_generate(self):
        res = super().action_generate()
        # Write number of volumes on picking (except pre-generated)
        pick_ids = self.vol_ids.filtered(lambda v: not v.picking_id.has_vol).mapped(
            "picking_id"
        )

        for pick_id in pick_ids:
            # Filter volumes that belong to the current picking
            vol_ids = self.vol_ids.search(
                [
                    ("picking_id", "=", pick_id.id),
                ]
            )
            volumes = vol_ids.mapped("nfe40_qVol")
            # Get the sum of volumes and assign it to the picking's number of volumes
            total_volumes = sum([float(v) for v in volumes])
            pick_id.number_of_volumes = total_volumes
        return res
