# Mauricio-ATS
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestDocumentEmail(TransactionCase):
    def test_compute_name_with_company(self):
        company = self.env.company

        document_type = self.env["l10n_br_fiscal.document.type"].create(
            {
                "name": "NFe",
                "code": "55",
                "type": "icms",
            }
        )

        mail_template = self.env["mail.template"].create(
            {
                "name": "NFe",
                "model_id": self.env.ref(
                    "l10n_br_fiscal.model_l10n_br_fiscal_document_email"
                ).id,
                "subject": "NFe - {{ object.name }}",
                "body_html": "<p>Esta é uma mensagem automática.</p>",
            }
        )

        record = self.env["l10n_br_fiscal.document.email"].create(
            {
                "document_type_id": document_type.id,
                "issuer": "company",
                "state_edoc": "autorizada",
                "email_template_id": mail_template.id,
                "company_id": company.id,
            }
        )

        expected = "NFe - autorizada - " + company.name
        self.assertEqual(record.name, expected)

    def test_no_duplicate_with_different_company(self):
        _logger.info(
            "Testando o método _compute_name do modelo l10n_br_fiscal.document.email"
            " em duas empresas diferentes"
        )
        company1 = self.env.company
        company2 = self.env["res.company"].create(
            {
                "name": "Outra Empresa",
            }
        )

        document_type = self.env["l10n_br_fiscal.document.type"].create(
            {
                "name": "NFe",
                "code": "55",
                "type": "icms",
            }
        )

        mail_template = self.env["mail.template"].create(
            {
                "name": "NFe",
                "model_id": self.env.ref(
                    "l10n_br_fiscal.model_l10n_br_fiscal_document_email"
                ).id,
                "subject": "NFe",
                "body_html": "<p>Mensagem</p>",
            }
        )

        vals = {
            "document_type_id": document_type.id,
            "issuer": "company",
            "state_edoc": "autorizada",
            "email_template_id": mail_template.id,
        }

        rec1 = self.env["l10n_br_fiscal.document.email"].create(
            {
                **vals,
                "company_id": company1.id,
            }
        )

        rec2 = self.env["l10n_br_fiscal.document.email"].create(
            {
                **vals,
                "company_id": company2.id,
            }
        )

        self.assertNotEqual(rec1.name, rec2.name)
