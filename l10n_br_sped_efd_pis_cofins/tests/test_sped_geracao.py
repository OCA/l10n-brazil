# Copyright 2026 KMEE
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0.html).

import base64
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.l10n_br_tax_assessment.tests.common_entrada import SpedEntradaCommon

from .test_sped_entrada import SpedPisCofinsEntradaMixin


@tagged("post_install", "-at_install")
class TestSpedPisCofinsGeneration(SpedPisCofinsEntradaMixin, SpedEntradaCommon):
    """The file is made of the registers of the moment of the generation, and a
    register that cannot be pulled stops it."""

    def _set_accountant(self, **vals):
        city = self.env["res.city"].search([("state_id.code", "=", "SP")], limit=1)
        self.company.accountant_id = self.env["res.partner"].create(
            {
                "name": "Accountant",
                "is_accountant": True,
                "cnpj_cpf": "111.444.777-35",
                "crc_code": "1SP123456/O-0",
                "email": "accountant@example.com",
                "country_id": self.env.ref("base.br").id,
                "state_id": self.env.ref("base.state_br_sp").id,
                "city_id": city.id,
                **vals,
            }
        )

    def _generated_text(self, declaration):
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", declaration._name), ("res_id", "=", declaration.id)],
            order="id desc",
            limit=1,
        )
        return base64.b64decode(attachment.datas).decode("latin-1")

    def test_the_file_has_the_registers_of_the_moment_of_the_generation(self):
        """Registers pulled before the accountant was registered: the 0100 comes
        in the file made after the registration was fixed."""
        self._entry_document()
        declaration = self._declaration_july()
        self.assertEqual(self._sped_records(declaration, "0100"), [])
        self._set_accountant()
        declaration.button_create_sped_files()
        self.assertIn("|0100|", self._generated_text(declaration))

    def test_a_register_that_cannot_be_pulled_stops_the_generation(self):
        """A register that fails to pull is only a note in the history and the
        file would go out without it: the generation stops with the reason."""
        self._set_accountant()
        self._entry_document()
        declaration = self._declaration_july()
        register = type(self.env["l10n_br_sped.efd_pis_cofins.0100"])

        def boom(self, *args, **kwargs):
            raise ValueError("boom")

        # a plain function: a Mock on the class is taken for an ondelete hook
        with mock.patch.object(register, "_map_from_odoo", boom):
            with self.assertRaises(UserError) as error:
                declaration.button_create_sped_files()
        self.assertIn("0100: boom", error.exception.args[0])

    def test_generation_stops_with_what_the_accountant_lacks(self):
        """The CRC is mandatory in the 0100 of the layout."""
        self._set_accountant(crc_code=False)
        self._entry_document()
        declaration = self._declaration_july()
        with self.assertRaises(UserError) as error:
            declaration.button_create_sped_files()
        self.assertIn("CRC", error.exception.args[0])
