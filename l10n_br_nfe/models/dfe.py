# Copyright (C) 2023 KMEE Informatica LTDA
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)

from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import models


class DFe(models.Model):
    _inherit = "l10n_br_fiscal.dfe"

    def parse_procNFe(self, xml):
        binding = TnfeProc.from_xml(xml.read().decode())
        return (
            self.env["nfe.40.infnfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding(binding.NFe.infNFe)
        )
