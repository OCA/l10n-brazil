# Copyright (C) 2026 KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class OperationCatalogCommon(TransactionCase):
    """Base para os testes do catálogo de operações fiscais.

    Fornece uma empresa em SP e três parceiros (interno, interestadual e
    exterior) para exercitar a resolução de CFOP por destino
    (``operation.line._get_cfop``), além de helpers de asserção.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.br = cls.env.ref("base.br")
        cls.state_sp = cls.env.ref("base.state_br_sp")
        cls.state_mg = cls.env.ref("base.state_br_mg")

        cls.company = cls.env.ref("base.main_company")
        cls.company.write({"country_id": cls.br.id, "state_id": cls.state_sp.id})

        Partner = cls.env["res.partner"]
        cls.partner_interno = Partner.create(
            {
                "name": "Parceiro Interno SP",
                "country_id": cls.br.id,
                "state_id": cls.state_sp.id,
            }
        )
        cls.partner_interestadual = Partner.create(
            {
                "name": "Parceiro Interestadual MG",
                "country_id": cls.br.id,
                "state_id": cls.state_mg.id,
            }
        )
        cls.partner_exterior = Partner.create(
            {
                "name": "Parceiro Exterior",
                "country_id": cls.env.ref("base.us").id,
            }
        )

    def _cfop_code(self, operation_line, partner):
        return operation_line._get_cfop(self.company, partner).code

    def assert_operation_cfops(
        self, operation_line_xmlid, internal, external, export=None
    ):
        """Confere que a linha de operação resolve o CFOP esperado por destino.

        :param operation_line_xmlid: xmlid completo da l10n_br_fiscal.operation.line
        :param internal: código CFOP esperado para operação interna (mesmo estado)
        :param external: código CFOP esperado para operação interestadual
        :param export: código CFOP esperado para exportação (opcional)
        """
        line = self.env.ref(operation_line_xmlid)
        self.assertEqual(
            self._cfop_code(line, self.partner_interno),
            internal,
            "CFOP interno incorreto em %s" % operation_line_xmlid,
        )
        self.assertEqual(
            self._cfop_code(line, self.partner_interestadual),
            external,
            "CFOP interestadual incorreto em %s" % operation_line_xmlid,
        )
        if export:
            self.assertEqual(
                self._cfop_code(line, self.partner_exterior),
                export,
                "CFOP de exportação incorreto em %s" % operation_line_xmlid,
            )

    def assert_return_link(self, operation_xmlid, return_operation_xmlid):
        """Confere o encadeamento remessa/retorno via return_fiscal_operation_id."""
        operation = self.env.ref(operation_xmlid)
        expected = self.env.ref(return_operation_xmlid)
        self.assertEqual(
            operation.return_fiscal_operation_id,
            expected,
            "Encadeamento de retorno incorreto em %s" % operation_xmlid,
        )
