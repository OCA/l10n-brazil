# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class DocumentLine(models.Model):
    """Export the IBS split produced by the RTC engine.

    ``l10n_br_nfe`` puts the whole IBS in ``gIBSUF`` and hardcodes
    ``gIBSMun`` to zero.  From 2027 the IBS is 0.05% state + 0.05%
    municipality, and from 2029 each State and Municipality sets its own
    rate, so the two groups must carry their own rate and value.
    """

    _inherit = "l10n_br_fiscal.document.line"

    def _rtc_split_export(self):
        self.ensure_one()
        return self.rtc_status == "calculated"

    def _export_tag_nfe_40_gibsuf(self, xsd_fields, class_obj, export_dict):
        if self._rtc_split_export():
            export_dict["pIBSUF"] = self.rtc_ibs_uf_percent
            export_dict["vIBSUF"] = self.rtc_ibs_uf_value
            return
        super()._export_tag_nfe_40_gibsuf(xsd_fields, class_obj, export_dict)

    def _export_tag_nfe_40_gibsuf_gred(self, xsd_fields, class_obj, export_dict):
        if self._rtc_split_export():
            if self.rtc_ibs_uf_reduction:
                export_dict["pRedAliq"] = self.rtc_ibs_uf_reduction
                export_dict["pAliqEfet"] = self.rtc_ibs_uf_percent * (
                    1 - self.rtc_ibs_uf_reduction / 100
                )
            return
        super()._export_tag_nfe_40_gibsuf_gred(xsd_fields, class_obj, export_dict)

    def _export_tag_nfe_40_gibsmun(self, xsd_fields, class_obj, export_dict):
        if self._rtc_split_export():
            export_dict["pIBSMun"] = f"{self.rtc_ibs_mun_percent:.4f}"
            export_dict["vIBSMun"] = f"{self.rtc_ibs_mun_value:.2f}"
            return
        super()._export_tag_nfe_40_gibsmun(xsd_fields, class_obj, export_dict)

    def _export_tag_nfe_40_gibsmun_gred(self, xsd_fields, class_obj, export_dict):
        # l10n_br_nfe has no hook here yet: the gRed group of gIBSMun is part
        # of the schema but never exported.  No super() to call on purpose.
        if not self._rtc_split_export():
            return
        if self.rtc_ibs_mun_reduction:
            export_dict["pRedAliq"] = self.rtc_ibs_mun_reduction
            export_dict["pAliqEfet"] = self.rtc_ibs_mun_percent * (
                1 - self.rtc_ibs_mun_reduction / 100
            )

    def _export_tag_nfe_40_gcbs(self, xsd_fields, class_obj, export_dict):
        if self._rtc_split_export():
            export_dict["pCBS"] = self.rtc_cbs_percent
            export_dict["vCBS"] = self.rtc_cbs_value
            return
        super()._export_tag_nfe_40_gcbs(xsd_fields, class_obj, export_dict)

    def _export_tag_nfe_40_gcbs_gred(self, xsd_fields, class_obj, export_dict):
        if self._rtc_split_export():
            if self.rtc_cbs_reduction:
                export_dict["pRedAliq"] = self.rtc_cbs_reduction
                export_dict["pAliqEfet"] = self.rtc_cbs_percent * (
                    1 - self.rtc_cbs_reduction / 100
                )
            return
        super()._export_tag_nfe_40_gcbs_gred(xsd_fields, class_obj, export_dict)
