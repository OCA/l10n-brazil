# Copyright 2025 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os
from datetime import datetime

from odoo.tests.common import TransactionCase
from odoo.tools import config


class TestCTeIBSCBS(TransactionCase):
    def test_cte_xml_includes_ibscbs_unescaped(self):
        """
        Ensure CT-e XML includes the IBSCBS tag with embedded inner XML (not escaped).

        The bindings represent IBSCBS as a Char field, so we build the inner XML
        string and unescape it after serialization.
        """

        cte = self.env.ref("l10n_br_cte.demo_cte_lc_modal_rodoviario")

        # Reset state for re-runs.
        if cte.state != "em_digitacao":
            cte.action_document_back2draft()

        # Minimal preparation (based on existing serialize tests).
        cte.fiscal_line_ids.name = "Frete"
        for line in cte.fiscal_line_ids:
            line.price_unit = 100
        cte.fiscal_line_ids.cfop_id = cte.env.ref("l10n_br_fiscal.cfop_5352")

        cte.action_document_confirm()
        cte.document_date = datetime.strptime(
            "2020-01-01T11:00:00",
            "%Y-%m-%dT%H:%M:%S",
        )
        cte.cte40_cCT = "57000111"

        # Required for modal rodoviario in serialize tests.
        cte.cte40_RNTRC = "12345678"

        # IBS/CBS setup (example values).
        tax_classification = self.env["l10n_br_fiscal.tax.classification"].create(
            {"code": "000001", "rate_type": "regular"}
        )
        ibs_cst = self.env.ref("l10n_br_fiscal.cst_ibs_000")

        # Apply to the first fiscal line (CT-e typically has a single service line).
        line = cte.fiscal_line_ids[:1]
        line.write(
            {
                "tax_classification_id": tax_classification.id,
                "ibs_cst_id": ibs_cst.id,
                "ibs_base": 15.80,
                "ibs_percent": 0.1000,
                "ibs_value": 0.02,
                "cbs_percent": 0.9000,
                "cbs_value": 0.14,
            }
        )

        cte._document_export()

        output_path = os.path.join(
            config["data_dir"],
            "filestore",
            self.cr.dbname,
            cte.send_file_id.store_fname,
        )
        with open(output_path, "rb") as f:
            xml = f.read().decode("utf-8")

        assert "<IBSCBS>" in xml
        assert "<CST>000</CST>" in xml
        assert "<cClassTrib>000001</cClassTrib>" in xml
        assert "<gIBSCBS>" in xml
        assert "<vBC>15.80</vBC>" in xml
        assert "<pIBSUF>0.1000</pIBSUF>" in xml
        assert "<vIBSUF>0.02</vIBSUF>" in xml
        assert "<pIBSMun>0.0000</pIBSMun>" in xml
        assert "<vIBSMun>0.00</vIBSMun>" in xml
        assert "<vIBS>0.02</vIBS>" in xml
        assert "<pCBS>0.9000</pCBS>" in xml
        assert "<vCBS>0.14</vCBS>" in xml

        # Ensure the embedded XML was not left escaped.
        assert "&lt;CST&gt;" not in xml
