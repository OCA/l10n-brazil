# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase

from ..tools import EdiParsedFile

KEY_1 = "35200159594315000157550010000000012062777161"
KEY_2 = "35200159594315000157550010000000022062777169"
KEY_3 = "35200159594315000157550010000000032062777166"


class EdiImportCase(TransactionCase):
    """Base of the tests that need an imported document, with no file to read."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.other_company = cls.env.ref("l10n_br_base.empresa_lucro_real")
        presumed = cls.env.ref("l10n_br_base.empresa_lucro_presumido")
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                allowed_company_ids=(cls.company | cls.other_company | presumed).ids,
            )
        )
        cls.Document = cls.env["l10n_br_fiscal.document"]
        cls.supplier = cls.env["res.partner"].create(
            {
                "name": "Supplier of the import",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_mg").id,
            }
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")

    def _parsed(self, key=KEY_1, company=None, status="authorized", **values):
        """What a reader would find in a file addressed to ``company``."""
        company = company or self.company
        vals = {
            "reader": "nfe",
            "document_type_code": "55",
            "access_key": key,
            "issuer_vat": "59594315000157",
            "company_vats": (("recipient", company.partner_id.cnpj_cpf_stripped),),
            "status": status,
            "status_code": "100" if status == "authorized" else "101",
            "binding": None,
            "file_name": f"{key}.xml",
            "content": f"<xml>{key}</xml>".encode(),
        }
        vals.update(values)
        return EdiParsedFile(**vals)

    def _create_imported_document(
        self, lines=None, partner=None, company=None, review=True, model=None, **values
    ):
        """A draft imported document, as the importer leaves it, with no file.

        :param lines: list of dicts of values of the lines (the defaults are one
            unit of "Imported item" at 10.00, declared in UN, CFOP 6102)
        :param review: start the review states of the lines
        :param model: the document model to create with (another user, a context)
        :param values: values of the document
        """
        lines = [{}] if lines is None else lines
        company = company or self.company
        vals = {
            "company_id": company.id,
            "document_type_id": self.env.ref("l10n_br_fiscal.document_55").id,
            "fiscal_operation_id": self.env.ref("l10n_br_fiscal.fo_compras").id,
            "imported_document": True,
            "issuer": "partner",
            "partner_id": (partner or self.supplier).id,
            "fiscal_line_ids": [
                (
                    0,
                    0,
                    dict(
                        {
                            "name": "Imported item",
                            "quantity": 1.0,
                            "price_unit": 10.0,
                            "uom_id": self.uom_unit.id,
                            "partner_uom_code": "UN",
                            "partner_cfop_id": self.env.ref(
                                "l10n_br_fiscal.cfop_6102"
                            ).id,
                        },
                        **line,
                    ),
                )
                for line in lines
            ],
        }
        vals.update(values)
        document = (
            (self.Document if model is None else model)
            .with_company(company)
            .create(vals)
        )
        if review:
            document._init_import_states()
        return document

    def _fiscal_user(self, login, companies=None):
        """A common fiscal user: not a manager, no right on purchases."""
        companies = companies or self.company
        return self.env["res.users"].create(
            {
                "name": f"User {login}",
                "login": login,
                "company_id": companies[:1].id,
                "company_ids": [(6, 0, companies.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_user").id,
                        ],
                    )
                ],
            }
        )
