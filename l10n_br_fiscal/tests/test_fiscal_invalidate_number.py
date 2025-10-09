# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestFiscalInvalidateNumber(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.company = cls.env.ref("l10n_br_base.empresa_simples_nacional")
        cls.document_type_nfe = cls.env.ref("l10n_br_fiscal.document_55")
        cls.document_serie_nfe = cls.env.ref("l10n_br_fiscal.empresa_sn_document_55_serie_1")

    def test_fiscal_invalidate_number(self):
        """Test Invalidate Number Overlap."""
        invalidate_number_100_200 = self.env["l10n_br_fiscal.invalidate.number"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type_nfe.id,
                "document_serie_id": self.document_serie_nfe.id,
                "number_start": 100,
                "number_end": 200,
                "justification": "Just a invalidate numbers test",
            }
        )
        invalidate_number_100_200.action_invalidate()

        invalidate_number_150_200 = self.env["l10n_br_fiscal.invalidate.number"].create(
            {
                "company_id": self.company.id,
                "document_type_id": self.document_type_nfe.id,
                "document_serie_id": self.document_serie_nfe.id,
                "number_start": 100,
                "number_end": 200,
                "justification": "Just a invalidate numbers test",
            }
        )

        