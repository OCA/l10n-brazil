# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal.constants.fiscal import PROCESSADOR_NENHUM


class TestDocumentCorrectionMessage(TransactionCase):
    def test_chatter_does_not_claim_the_letter_was_registered(self):
        """The tax authority may still refuse a letter that was requested."""
        company = self.env.ref("l10n_br_base.empresa_lucro_presumido")
        company.processador_edoc = PROCESSADOR_NENHUM
        document = self.env["l10n_br_fiscal.document"].create(
            {
                "company_id": company.id,
                "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            }
        )
        document._document_correction("Where it reads X, read Y")
        self.assertIn("Correction letter requested", document.message_ids[0].body)
