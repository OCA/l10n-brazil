# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date

from odoo.addons.l10n_br_fiscal_edi.tools import EdiInstallment

from .test_cte_serialize import TestCTeSerialize

_logger = logging.getLogger(__name__)


class TestCTeExportCollection(TestCTeSerialize):
    """The XML of a CT-e issued from an invoice on terms carries the collection
    (cobr) with the invoice and one duplicate for each installment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass(
            [
                {
                    "record_ref": "l10n_br_cte.demo_cte_lc_modal_rodoviario",
                    "xml_file": (
                        "CTe35240781583054000129570010000057311040645894-cobr.xml"
                    ),
                }
            ]
        )

    @classmethod
    def prepare_test_cte(cls, cte):
        if cte.state_edoc != "em_digitacao":  # 2nd test run
            cte.action_document_back2draft()
        cte.fiscal_line_ids.name = "Frete"
        cte.fiscal_line_ids.price_unit = 100
        # what the posting of the invoice does, with due dates that never pass
        cte._edi_set_installments(
            [
                EdiInstallment("001", date(2099, 1, 10), 40.0),
                EdiInstallment("002", date(2099, 2, 10), 60.0),
            ]
        )
        return super().prepare_test_cte(cte)

    def test_serialize_xml(self):
        for cte_data in self.cte_list:
            diff = self.serialize_xml(cte_data)
            _logger.info(f"Diff with expected XML (if any): {diff}")
            self.assertEqual(len(diff), 0)
