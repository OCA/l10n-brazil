# Copyright (C) 2024 Diego Paradeda - KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_vol = fields.Boolean(
        string="Has Vol IDs",
        help="Technical Field: True if the picking has already generated Volume IDs.",
        copy=False,
    )

    vol_ids = fields.One2many(
        string="Volume Data",
        comodel_name="stock.picking.vol",
        inverse_name="picking_id",
        copy=False,
    )

    number_of_volumes = fields.Integer(
        string="Number of Volumes",
        default=0,
        copy=False,
    )

    def _get_volume_data_package_level(self):
        """Generate a single volume for packages"""
        vols_data = []
        for picking_id in self:
            if picking_id.package_ids:
                for package_level_id in picking_id.package_level_ids:
                    manual_weight = package_level_id.package_id.shipping_weight
                    vol_data = {
                        "nfe40_qVol": 1,
                        "nfe40_esp": "",
                        "nfe40_marca": "",
                        "nfe40_pesoL": 0,
                        "nfe40_pesoB": (manual_weight if manual_weight else 0),
                        "picking_id": picking_id.id,
                    }

                    for line in package_level_id.move_line_ids:
                        vol_data["nfe40_esp"] = (
                            vol_data["nfe40_esp"] or line.product_id.product_volume_type
                        )
                        product_nfe40_marca = (
                            line.product_id.product_brand_id.name
                            if line.product_id.product_brand_id
                            else ""
                        )
                        vol_data["nfe40_marca"] = (
                            vol_data["nfe40_marca"] or product_nfe40_marca
                        )
                        pesoL = line.qty_done * line.product_id.net_weight
                        pesoB = line.qty_done * line.product_id.weight
                        vol_data["nfe40_pesoL"] += pesoL
                        vol_data["nfe40_pesoB"] += 0 if manual_weight else pesoB
                    vols_data.append(vol_data)

        return vols_data

    def _get_volume_data_wo_package(self):
        """Generate a single volume for lines without package"""
        vols_data = []
        for picking_id in self:
            # Filter out move lines with in a package
            if not picking_id.move_line_ids_without_package.filtered(
                lambda ml: not ml.package_level_id
            ):
                continue

            new_vol = {
                "nfe40_qVol": 0,
                "nfe40_esp": "",
                "nfe40_marca": "",
                "nfe40_pesoL": 0,
                "nfe40_pesoB": 0,
                "picking_id": picking_id.id,
            }

            for line in picking_id.move_line_ids_without_package.filtered(
                lambda ml: not ml.package_level_id and not ml.result_package_id
            ):
                new_vol["nfe40_qVol"] += line.qty_done
                new_vol["nfe40_esp"] = (
                    new_vol["nfe40_esp"] or line.product_id.product_volume_type
                )
                product_nfe40_marca = (
                    line.product_id.product_brand_id.name
                    if line.product_id.product_brand_id
                    else ""
                )
                new_vol["nfe40_marca"] = new_vol["nfe40_marca"] or product_nfe40_marca
                pesoL = line.qty_done * line.product_id.net_weight
                pesoB = line.qty_done * line.product_id.weight
                new_vol["nfe40_pesoL"] += pesoL
                new_vol["nfe40_pesoB"] += pesoB

            new_vol["nfe40_qVol"] = f"{new_vol['nfe40_qVol']:.0f}"
            vols_data.append(new_vol)

        return vols_data

    def _get_pre_generated_volumes(self):
        """Retreive and convert already generated volumes that are stored on picking"""
        vols_data = []
        for picking_id in self:
            for vol_id in picking_id.vol_ids:
                vol_data = vol_id.copy_data()[0]
                vols_data.append(vol_data)
        return vols_data

    def prepare_vols_data_from_picking(self):
        pre_generated_pickings = self.filtered(lambda p: p.has_vol)
        to_generate_pickings = self.filtered(lambda p: not p.has_vol)

        vols_data = []
        vols_data += pre_generated_pickings._get_pre_generated_volumes()
        vols_data += to_generate_pickings._get_volume_data_package_level()
        vols_data += to_generate_pickings._get_volume_data_wo_package()
        return vols_data

    def _compute_number_of_volumes(self):
        for picking in self:
            if len(picking.invoice_ids) == 1:
                picking.number_of_volumes = sum(
                    [
                        float(v)
                        for v in picking.invoice_ids.mapped(
                            "fiscal_document_id.nfe40_vol.nfe40_qVol"
                        )
                    ]
                )
            else:
                picking.number_of_volumes = 0
