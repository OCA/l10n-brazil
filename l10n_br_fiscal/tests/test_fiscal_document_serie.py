# Copyright (C) 2025  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger


class TestFiscalDocumentSerie(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Company
        cls.company_sn = cls.env.ref("l10n_br_base.empresa_simples_nacional")

        # Fiscal Document Type
        cls.document_type_nfe = cls.env.ref("l10n_br_fiscal.document_55")

        cls.document_serie_nfe_5 = cls.env["l10n_br_fiscal.document.serie"].create(
            {
                "code": "5",
                "name": "Serie 5",
                "document_type_id": cls.document_type_nfe.id,
                "company_id": cls.company_sn.id,
            }
        )

        # Fiscal Document
        cls.document = cls.env["l10n_br_fiscal.document"].create(
            {
                "company_id": cls.company_sn.id,
                "document_type_id": cls.document_type_nfe.id,
                "document_serie_id": cls.document_serie_nfe_5.id,
                "partner_id": cls.env.ref("l10n_br_base.res_partner_cliente1_sp").id,
                "state_edoc": "cancelada",
            }
        )

    def test_document_serie_duplicated(self):
        """Test document serie duplicate constraint."""
        document_serie = self.env["l10n_br_fiscal.document.serie"]
        document_serie_values = {
            "code": "10",
            "name": "Serie 10",
            "document_type_id": self.document_type_nfe.id,
            "company_id": self.company_sn.id,
        }

        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            for _ in range(2):
                document_serie.create(document_serie_values)

    def test_document_serie_code_in_use(self):
        """Test document serie code in use constraint."""
        with self.assertRaises(ValidationError):
            self.document_serie_nfe_5.write({"code": "7"})
