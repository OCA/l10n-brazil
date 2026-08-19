# Copyright (C) 2026  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import base64
import io
import zipfile

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase

from odoo.addons.l10n_br_fiscal_fci.constants import (
    FCI_FIELD_SEPARATOR,
    FCI_FILE_ENCODING,
    FCI_UTF8_STANDARD_TEXT,
)

FCI_CODE = "D1B1EAD4-5AEF-4648-A5E3-A5EB391B19BB"


class TestFCI(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.ncm = cls._get_ncm("8407.34.90", "Motores de pistão alternativo")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Motor de pistão por ignição - R123-A4-5",
                "default_code": "12j8ai.5d0-ao4p",
                "barcode": "07123456789012",
                "ncm_id": cls.ncm.id,
            }
        )
        cls.fci = cls.env["l10n_br_fiscal.fci.header"].create(
            {
                "company_id": cls.company.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "name": "Motor de pistão por ignição, "
                            "cilindrada igual à 2.000 cm³ - R123-A4-5",
                            "uom_code": "unid",
                            "amount_interstate": 9123.45,
                            "amount_imported": 4567.89,
                        },
                    )
                ],
            }
        )
        cls.line = cls.fci.line_ids

    @classmethod
    def _get_ncm(cls, code, name):
        """Return the NCM of the given code, creating it when missing.

        The NCM table is loaded by l10n_br_fiscal but the tests must not
        rely on a given NCM being present in the database.
        """
        ncm = cls.env["l10n_br_fiscal.ncm"].search([("code", "=", code)], limit=1)
        return ncm or cls.env["l10n_br_fiscal.ncm"].create({"code": code, "name": name})

    def _file_lines(self, fci):
        return base64.b64decode(fci.file).decode(FCI_FILE_ENCODING).splitlines()

    def test_import_content(self):
        """The import content follows the ROUND(x;y) rule of the manual."""
        self.assertAlmostEqual(self.line.import_content, 50.07, places=2)
        for imported, interstate, expected in (
            (4821.09, 6572.84, 73.35),
            (9043.46, 9103.69, 99.34),
            (93.94, 2803.12, 3.35),
            (10789.00, 52462.92, 20.57),
            (6789.00, 32996.35, 20.58),
        ):
            self.line.write(
                {
                    "amount_imported": imported,
                    "amount_interstate": interstate,
                }
            )
            self.assertAlmostEqual(self.line.import_content, expected, places=2)

    def test_line_defaults_from_product(self):
        """The goods data is taken from the product."""
        self.assertEqual(self.line.ncm_id, self.ncm)
        self.assertEqual(self.line.ncm_code, "84073490")
        self.assertEqual(self.line.product_code, "12j8ai.5d0-ao4p")
        self.assertEqual(self.line.gtin, "07123456789012")

    def test_check_ncm(self):
        """A NCM starting with two zeros is refused."""
        ncm = self._get_ncm("0000.00.00", "Sem NCM")
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.line.ncm_id = ncm

    def test_check_amounts(self):
        """Amounts equal to zero are refused."""
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.line.amount_interstate = 0.0
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.line.amount_imported = 0.0

    def test_generate_file(self):
        """The generated file follows the layout of the Ato COTEPE 61/2012."""
        self.fci.action_generate_file()
        self.assertEqual(self.fci.state, "generated")
        lines = self._file_lines(self.fci)

        # one register 0000, 0001, 0010, 0990, 5001, 5020, 5990, 9001,
        # three 9900, 9990 and 9999
        self.assertEqual(len(lines), 13)

        cnpj = "97231608000169"
        self.assertEqual(
            lines[0], FCI_FIELD_SEPARATOR.join(["0000", cnpj, self.company.name, "1.0"])
        )
        self.assertEqual(lines[1], f"0001{FCI_FIELD_SEPARATOR}{FCI_UTF8_STANDARD_TEXT}")

        register_0010 = lines[2].split(FCI_FIELD_SEPARATOR)
        self.assertEqual(register_0010[0], "0010")
        self.assertEqual(register_0010[1], cnpj)
        self.assertEqual(register_0010[2], self.company.legal_name)
        self.assertEqual(register_0010[3], "454504604553")
        self.assertEqual(register_0010[5], "01311000")
        self.assertEqual(register_0010[7], "SP")

        self.assertEqual(lines[3], "0990|4")
        self.assertEqual(lines[4], "5001")
        self.assertEqual(
            lines[5],
            "5020|Motor de pistão por ignição, cilindrada igual à 2.000 cm³ "
            "- R123-A4-5|84073490|12j8ai.5d0-ao4p|07123456789012|unid|"
            "9123,45|4567,89|50,07",
        )
        self.assertEqual(lines[6], "5990|3")
        self.assertEqual(lines[7], "9001")
        self.assertEqual(lines[8], "9900|0000|1")
        self.assertEqual(lines[9], "9900|0010|1")
        self.assertEqual(lines[10], "9900|5020|1")
        self.assertEqual(lines[11], "9990|5")
        self.assertEqual(lines[12], "9999|13")

        self.assertTrue(self.fci.filename.startswith(f"{cnpj}_"))
        self.assertTrue(self.fci.filename.endswith(".txt"))

    def test_generate_file_several_goods(self):
        """The block 9 totalizes every register 5020 of the file."""
        product = self.env["product.product"].create(
            {
                "name": "Motor elétrico ABC - H10-20-300",
                "default_code": "abc-1234",
                "ncm_id": self.ncm.id,
            }
        )
        self.fci.write(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "uom_code": "unid",
                            "amount_interstate": 345.67,
                            "amount_imported": 123.45,
                        },
                    )
                ]
            }
        )
        self.fci.action_generate_file()
        lines = self._file_lines(self.fci)
        self.assertEqual(len(lines), 14)
        self.assertEqual(lines[7], "5990|4")
        self.assertIn("9900|5020|2", lines)
        self.assertEqual(lines[-1], "9999|14")

    def test_generate_file_without_lines(self):
        """A FCI without goods can not be generated."""
        fci = self.env["l10n_br_fiscal.fci.header"].create(
            {"company_id": self.company.id}
        )
        with self.assertRaises(UserError):
            fci.action_generate_file()

    def test_workflow(self):
        """The FCI can only be transmitted after the file generation."""
        self.fci.action_generate_file()
        with self.assertRaises(UserError):
            self.fci.action_set_transmitted()
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()
        self.assertEqual(self.fci.state, "transmitted")
        # a transmitted FCI can neither be set back to draft nor deleted
        with self.assertRaises(UserError), self.cr.savepoint():
            self.fci.action_back_to_draft()
        with self.assertRaises(UserError), self.cr.savepoint():
            self.fci.unlink()

    def test_back_to_draft(self):
        """The file can be dropped while there is no FCI control number."""
        self.fci.action_generate_file()
        self.fci.action_back_to_draft()
        self.assertEqual(self.fci.state, "draft")
        self.assertFalse(self.fci.file)
        self.fci.action_generate_file()
        self.line.fci_code = FCI_CODE
        with self.assertRaises(UserError):
            self.fci.action_back_to_draft()

    def _prepare_return_file(
        self,
        fci_code=FCI_CODE,
        validation="100",
        hash_code="52-25-82-C0-0E-36-6C-7F-72-68-AA-92-7E-EB-D7-FF",
    ):
        """Build a return file from the transmitted one."""
        lines = []
        for file_line in self._file_lines(self.fci):
            values = file_line.split(FCI_FIELD_SEPARATOR)
            if values[0] == "0000":
                values += [
                    hash_code,
                    "09/01/2013 16:30:46",
                    "11111",
                    "09/01/2013 16:42:42",
                    "0 - Arquivo recebido com sucesso!",
                ]
            elif values[0] == "5020":
                values += [fci_code, validation]
            lines.append(FCI_FIELD_SEPARATOR.join(values))
        return base64.b64encode("\r\n".join(lines).encode(FCI_FILE_ENCODING))

    def _run_wizard(self, file_data, filename="fci.txt", fci=None):
        values = {"file": file_data, "filename": filename}
        if fci is not None:
            values["fci_id"] = fci.id
        wizard = self.env["l10n_br_fiscal.fci.import.wizard"].create(values)
        wizard.action_import()
        return wizard

    def _import_return_file(self, **kwargs):
        wizard = (
            self.env["l10n_br_fiscal.fci.import.wizard"]
            .with_context(
                active_model="l10n_br_fiscal.fci.header", active_id=self.fci.id
            )
            .create(
                {
                    "file": self._prepare_return_file(**kwargs),
                    "filename": "return.txt",
                }
            )
        )
        wizard.action_import()
        return wizard

    def test_import_return_file(self):
        """The FCI control numbers are read from the return file."""
        self.fci.action_generate_file()
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()

        wizard = self._import_return_file()

        self.assertEqual(wizard.fci_id, self.fci)
        self.assertEqual(self.fci.state, "done")
        self.assertEqual(self.fci.protocol_number, "11111")
        self.assertEqual(self.fci.date_reception, "09/01/2013 16:30:46")
        self.assertEqual(self.fci.hash_code[:2], "52")
        self.assertEqual(self.fci.return_filename, "return.txt")
        self.assertEqual(self.line.fci_code, FCI_CODE)
        self.assertEqual(self.line.validation_indicator, "100")
        self.assertEqual(self.product.product_tmpl_id.fci_code, FCI_CODE)

    def test_import_return_file_rejected(self):
        """A goods rejected by the tax administration has no FCI number."""
        self.fci.action_generate_file()
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()

        self._import_return_file(fci_code="", validation="200")

        self.assertFalse(self.line.fci_code)
        self.assertEqual(self.line.validation_indicator, "200")
        self.assertEqual(self.fci.state, "transmitted")

    def test_import_return_file_draft(self):
        """There is no return file to import for a draft FCI."""
        self.fci.action_generate_file()
        return_file = self._prepare_return_file()
        self.fci.action_back_to_draft()
        wizard = self.env["l10n_br_fiscal.fci.import.wizard"].create(
            {
                "fci_id": self.fci.id,
                "file": return_file,
                "filename": "return.txt",
            }
        )
        with self.assertRaises(UserError):
            wizard.action_import()

    def test_import_transmission_file(self):
        """A file generated in another platform is imported as a draft FCI."""
        self.fci.action_generate_file()
        transmission_file = self.fci.file
        # the goods of the imported file are matched with the products
        # through their internal code
        self.fci.action_back_to_draft()
        self.fci.unlink()

        wizard = self._run_wizard(
            transmission_file, "97231608000169_20260101_120000.txt"
        )
        fci = wizard.fci_id

        self.assertEqual(fci.state, "draft")
        self.assertEqual(fci.company_id, self.company)
        self.assertEqual(len(fci.line_ids), 1)
        line = fci.line_ids
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.ncm_id, self.ncm)
        self.assertEqual(line.product_code, "12j8ai.5d0-ao4p")
        self.assertEqual(line.gtin, "07123456789012")
        self.assertEqual(line.uom_code, "unid")
        self.assertEqual(line.amount_interstate, 9123.45)
        self.assertEqual(line.amount_imported, 4567.89)
        self.assertAlmostEqual(line.import_content, 50.07, places=2)
        # the imported FCI generates the very same file
        fci.action_generate_file()
        self.assertEqual(
            base64.b64decode(fci.file).decode(FCI_FILE_ENCODING),
            base64.b64decode(transmission_file).decode(FCI_FILE_ENCODING),
        )

    def test_import_transmission_file_unknown_product(self):
        """The goods without a matching product are imported anyway."""
        self.fci.action_generate_file()
        transmission_file = self.fci.file
        self.fci.action_back_to_draft()
        self.fci.unlink()
        self.product.default_code = "another-code"
        self.product.barcode = False

        wizard = self._run_wizard(transmission_file)

        self.assertFalse(wizard.fci_id.line_ids.product_id)
        self.assertIn("12j8ai.5d0-ao4p", wizard.result)
        # a goods without product still holds the data of the file
        self.assertEqual(wizard.fci_id.line_ids.ncm_id, self.ncm)

    def test_import_return_file_new_fci(self):
        """A return file of a FCI which is not in the database creates it."""
        self.fci.action_generate_file()
        return_file = self._prepare_return_file()
        self.fci.action_back_to_draft()
        self.fci.unlink()

        wizard = self._run_wizard(return_file, "return.txt")
        fci = wizard.fci_id

        self.assertEqual(fci.state, "done")
        self.assertEqual(fci.protocol_number, "11111")
        self.assertEqual(fci.line_ids.fci_code, FCI_CODE)
        self.assertEqual(fci.line_ids.product_id, self.product)
        self.assertEqual(self.product.product_tmpl_id.fci_code, FCI_CODE)

    def test_import_return_file_existing_fci(self):
        """A return file uploaded from the list updates the FCI it comes
        from instead of creating a second one."""
        self.fci.action_generate_file()
        # the hash code is only known once the return file is downloaded,
        # so the FCI is matched by the reception protocol typed by the user
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()
        self.assertFalse(self.fci.hash_code)
        return_file = self._prepare_return_file()

        wizard = self._run_wizard(return_file, "return.txt")

        self.assertEqual(wizard.fci_id, self.fci)
        self.assertEqual(self.fci.line_ids.fci_code, FCI_CODE)
        self.assertTrue(self.fci.hash_code)
        self.assertEqual(
            self.env["l10n_br_fiscal.fci.header"].search_count(
                [("protocol_number", "=", "11111")]
            ),
            1,
        )

    def test_import_transmission_file_on_existing_fci(self):
        """A file without FCI control number can not update a FCI."""
        self.fci.action_generate_file()
        transmission_file = self.fci.file
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()
        with self.assertRaises(UserError):
            self._run_wizard(transmission_file, "fci.txt", fci=self.fci)

    def test_import_unknown_company(self):
        """A file of another CNPJ is refused."""
        self.fci.action_generate_file()
        transmission_file = base64.b64encode(
            base64.b64decode(self.fci.file)
            .decode(FCI_FILE_ENCODING)
            .replace("97231608000169", "46377222000129")
            .encode(FCI_FILE_ENCODING)
        )
        self.fci.action_back_to_draft()
        self.fci.unlink()
        with self.assertRaises(UserError):
            self._run_wizard(transmission_file)

    def test_import_invalid_file(self):
        """A file which is not a FCI file is refused."""
        with self.assertRaises(UserError):
            self._run_wizard(base64.b64encode(b"not a FCI file"))

    def test_import_return_file_zip(self):
        """The ZIP downloaded from the FCI web system is accepted."""
        self.fci.action_generate_file()
        self.fci.protocol_number = "11111"
        self.fci.action_set_transmitted()
        return_file = base64.b64decode(self._prepare_return_file())

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("97231608000169_20130109_152540.txt", return_file)

        wizard = self._run_wizard(
            base64.b64encode(archive.getvalue()),
            "97231608000169_20130109_152540.zip",
            fci=self.fci,
        )

        self.assertEqual(wizard.fci_id, self.fci)
        self.assertEqual(self.fci.state, "done")
        self.assertEqual(self.line.fci_code, FCI_CODE)

    def test_import_zip_without_txt(self):
        """A ZIP without a TXT file inside is refused."""
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as zip_file:
            zip_file.writestr("readme.pdf", b"not a FCI file")
        with self.assertRaises(UserError):
            self._run_wizard(base64.b64encode(archive.getvalue()), "return.zip")
