# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class StockGenerateVolumes(models.TransientModel):
    """
    This wizard allows for the pre-generation of picking volumes. If triggered, the
    field 'stock_picking.field_vol_ids' will be populated and later replicated in the
    'nfe40_vol' field.
    If not triggered, the volumes will be automatically generated during the invoice
    creation process (in 'stock.invoice.onshipping').
    """

    _name = "stock.generate.volumes"
    _description = "Stock Generate Volumes"

    vol_ids = fields.One2many(
        string="Volume Data",
        comodel_name="stock.invoice.onshipping.vol",
        inverse_name="generate_vols_wizard_id",
    )

    def _load_picking_id(self):
        picking_obj = self.env["stock.picking"]
        active_ids = self.env.context.get("active_ids", [])
        picking_id = picking_obj.browse(active_ids)[0]
        if not picking_id:
            raise UserError(_("No picking to generate vols!"))
        return picking_id

    @api.model
    def default_get(self, fields_list):
        """
        Inherit to add default vol_ids
        :param fields_list: list of str
        :return: dict
        """
        result = super().default_get(fields_list)

        picking_id = self._load_picking_id()
        vols_data = picking_id.prepare_vols_data_from_picking()
        vol_ids = [Command.create(vol) for vol in vols_data]

        result["vol_ids"] = vol_ids
        return result

    def action_generate(self):
        """
        Launch the volume generation
        :return:
        """
        self.ensure_one()
        picking_id = self._load_picking_id()

        # Update the volume generation state on pickings
        picking_id.has_vol = True

        volume_data = []
        for vol_id in self.vol_ids:
            vol_data = vol_id.copy_data({"picking_id": picking_id.id})[0]
            vol_data.pop("invoice_wizard_id", None)
            vol_data.pop("generate_vols_wizard_id", None)
            volume_data.append(vol_data)

        new_picks = picking_id.vol_ids.create(volume_data)
        picking_id.number_of_volumes = sum(
            [float(v) for v in new_picks.mapped("nfe40_qVol")]
        )
