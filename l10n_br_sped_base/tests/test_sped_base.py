# Copyright 2024 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import base64
from collections import defaultdict
from datetime import date, datetime
from io import StringIO
from os import path
from unittest import mock
from unittest.mock import patch

from erpbrasil.base import misc
from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase
from odoo.tools import mute_logger
from odoo.tools.translate import code_translations

from odoo.addons import l10n_br_sped_base
from odoo.addons.l10n_br_sped_base.models.sped_mixin import SPED_ENCODING

from .test_sped_document import SpedDocumentCommon


class TestSpedBase(SpedDocumentCommon, TransactionCase, FakeModelLoader):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        cls.addClassCleanup(cls.loader.restore_registry)

        # import simpilified equivalent of SPED ECD models:
        from .sped_fake import (
            Registro0000,
            Registro0007,
            RegistroI010,
            RegistroI012,
            RegistroI015,
            RegistroI030,
            RegistroI050,
            RegistroI510,
            RegistroI550,
            RegistroI555,
            RegistroJ900,
            RegistroJ930,
        )
        from .sped_fake_spec_9 import (
            Registro0000 as AbstractRegistro0000,
        )
        from .sped_fake_spec_9 import (
            Registro0007 as AbstractRegistro0007,
        )
        from .sped_fake_spec_9 import (
            RegistroI010 as AbstractRegistroI010,
        )
        from .sped_fake_spec_9 import (
            RegistroI012 as AbstractRegistroI012,
        )
        from .sped_fake_spec_9 import (
            RegistroI015 as AbstractRegistroI015,
        )
        from .sped_fake_spec_9 import (
            RegistroI030 as AbstractRegistroI030,
        )
        from .sped_fake_spec_9 import (
            RegistroI050 as AbstractRegistroI050,
        )
        from .sped_fake_spec_9 import (
            RegistroI510 as AbstractRegistroI510,
        )
        from .sped_fake_spec_9 import (
            RegistroI550 as AbstractRegistroI550,
        )
        from .sped_fake_spec_9 import (
            RegistroI555 as AbstractRegistroI555,
        )
        from .sped_fake_spec_9 import (
            RegistroJ900 as AbstractRegistroJ900,
        )
        from .sped_fake_spec_9 import (
            RegistroJ930 as AbstractRegistroJ930,
        )
        from .sped_mixin_fake import SpecMixinFAKE

        cls.loader.update_registry(
            (
                SpecMixinFAKE,
                AbstractRegistro0000,
                AbstractRegistro0007,
                AbstractRegistroI010,
                AbstractRegistroI012,
                AbstractRegistroI015,
                AbstractRegistroI030,
                AbstractRegistroI050,
                AbstractRegistroI510,
                AbstractRegistroI550,
                AbstractRegistroI555,
                AbstractRegistroJ900,
                AbstractRegistroJ930,
                Registro0000,
                Registro0007,
                RegistroI010,
                RegistroI012,
                RegistroI015,
                RegistroI030,
                RegistroI050,
                RegistroI510,
                RegistroI550,
                RegistroI555,
                RegistroJ900,
                RegistroJ930,
            )
        )
        # TransactionCase.setUpClass took the snapshot of the model attributes
        # that check_attrs compares after every test, before the fake models
        # existed: take it again now that they are loaded.
        default_attrs = cls.attrs_before["base"]
        for model in cls.registry.values():
            cls.attrs_before.setdefault(model._name, set(default_attrs)).update(
                vars(model)
            )
        demo_path = path.join(l10n_br_sped_base.__path__[0], "tests")
        cls.file_path = path.join(demo_path, "demo_fake.txt")
        sped_mixin = cls.env["l10n_br_sped.mixin"]
        sped_mixin._flush_registers("fake")
        cls.declaration = sped_mixin._import_file(cls.file_path, "fake")

    def test_register_line_uses_the_concrete_field(self):
        """Field attributes come from the concrete model, not from the spec.

        The field ORDER must keep coming from the spec, which is the layout,
        but the attributes must not: the generated spec does not carry the
        mandatoriness the Guia Pratico defines, so the mapping layer declares
        it. While the writer read the spec, a field declared `required=True`
        in the mapping was ignored and every zeroed amount came out blank,
        which the PVA rejects with "mandatory field".
        """
        register = self.declaration
        spec = self.env["l10n_br_sped.fake.9.0000"]
        seen = []
        original = type(register)._format_field_value

        def spy(self_, field, value):
            seen.append(field)
            return original(self_, field, value)

        with mock.patch.object(
            type(register), "_format_field_value", autospec=True, side_effect=spy
        ):
            register._generate_register_text(StringIO(), "9", [0], defaultdict(int))

        self.assertTrue(seen, "no field was written")
        for field in seen:
            name = field.name
            self.assertIs(
                field,
                register._fields[name],
                f"{name} was taken from the spec instead of the concrete model",
            )
            # the spec holds a different Field instance for the same name, so
            # the assertion above really distinguishes the two
            self.assertIsNot(field, spec._fields[name])

    def test_block_movement_counts_only_this_declaration(self):
        """The block movement indicator looks at this declaration alone.

        With `search_count([])` a second, empty declaration opened its blocks
        as "has data" because the count saw the registers of the first one, and
        the PVA rejects the import in that case with "the block opening record
        states the block has movement, however no record was reported in the
        block".
        """
        source = self.declaration
        other = self.env["l10n_br_sped.fake.0000"].create(
            {
                "company_id": source.company_id.id,
                "DT_INI": "2022-01-01",
                "DT_FIN": "2022-12-31",
                "LECD": source.LECD,
                "NOME": source.NOME,
                "CNPJ": source.CNPJ,
                "UF": source.UF,
                "IND_SIT_INI_PER": source.IND_SIT_INI_PER,
                "IND_NIRE": source.IND_NIRE,
                "IND_FIN_ESC": source.IND_FIN_ESC,
                "IND_GRANDE_PORTE": source.IND_GRANDE_PORTE,
                "TIP_ECD": source.TIP_ECD,
                "IDENT_MF": source.IDENT_MF,
                "IND_ESC_CONS": source.IND_ESC_CONS,
                "IND_CENTRALIZADA": source.IND_CENTRALIZADA,
                "IND_MUDANC_PC": source.IND_MUDANC_PC,
            }
        )
        # the guard that makes this test meaningful: without a register of
        # block I somewhere else in the database, a naive count would also
        # report "no movement" and the test would pass either way
        self.assertTrue(
            self.env["l10n_br_sped.fake.i010"].search_count([]),
            "the fixture must have block I registers for this test to mean " "anything",
        )
        sped = other._generate_sped_text()

        # the fixture declaration does have I and J registers, so a count
        # without the declaration domain would open both blocks here
        for bloco in ("I", "J"):
            self.assertIn(
                f"|{bloco}001|1|",
                sped,
                f"block {bloco} is empty in this declaration and must open "
                f"with no movement",
            )

    def test_skip_empty_blocks(self):
        """With the hook on, a block with no records is left out of the file."""
        source = self.declaration
        other = self.env["l10n_br_sped.fake.0000"].create(
            {
                "company_id": source.company_id.id,
                "DT_INI": "2022-01-01",
                "DT_FIN": "2022-12-31",
                "LECD": source.LECD,
                "NOME": source.NOME,
                "CNPJ": source.CNPJ,
                "UF": source.UF,
                "IND_SIT_INI_PER": source.IND_SIT_INI_PER,
                "IND_NIRE": source.IND_NIRE,
                "IND_FIN_ESC": source.IND_FIN_ESC,
                "IND_GRANDE_PORTE": source.IND_GRANDE_PORTE,
                "TIP_ECD": source.TIP_ECD,
                "IDENT_MF": source.IDENT_MF,
                "IND_ESC_CONS": source.IND_ESC_CONS,
                "IND_CENTRALIZADA": source.IND_CENTRALIZADA,
                "IND_MUDANC_PC": source.IND_MUDANC_PC,
            }
        )
        with patch.object(type(other), "_skip_empty_blocks", return_value=True):
            lines = other._generate_sped_text().splitlines()
        self.assertFalse([ln for ln in lines if ln.startswith(("|I", "|J"))])
        self.assertNotIn("|9900|I001|1|", lines)
        self.assertEqual(lines[-1], f"|9999|{len(lines)}|")

    def test_generate_sped(self):
        sped = self.declaration._generate_sped_text()
        with open(self.file_path, encoding=SPED_ENCODING) as f:
            target_content = f.read()
            # print(sped)
            self.assertEqual(sped.strip(), target_content.strip())
        self.assertEqual(len(self.declaration._split_sped_text_by_bloco(sped)), 2)

    def test_register_tree_view(self):
        arch = self.env["l10n_br_sped.fake.i010"].get_view(view_type="tree")["arch"]
        self.assertIn(  # link to declaration
            '<field name="declaration_id"',
            arch,
        )

        self.assertIn(  # simple SPED field
            '<field name="IND_ESC"',
            arch,
        )

    def test_register_form_view(self):
        arch = self.env["l10n_br_sped.fake.i010"].get_view(view_type="form")["arch"]
        self.assertIn(  # link to declaration
            '<field name="declaration_id"',
            arch,
        )

        self.assertIn(  # link to Odoo record if any
            '<field name="reference"',
            arch,
        )

        self.assertIn(  # simple SPED field
            '<field name="IND_ESC"',
            arch,
        )

        self.assertIn(  # o2m SPED child
            '<field name="reg_I050_ids"',
            arch,
        )
        self.assertNotIn("attrs=", arch)

    def test_format_field_value(self):
        """An amount always carries two decimals; a quantity is not rounded."""
        mixin_instance = self.env["l10n_br_sped.fake.9.0000"]

        # --- Monetary ---
        mock_monetary_field = mock.Mock()
        mock_monetary_field.type = "monetary"

        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 789.123),
            "789,12",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 789.00),
            "789,00",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 17500.0),
            "17500,00",
        )
        # A negative value keeps its sign
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, -15.5),
            "-15,50",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 0.0),
            "",
        )

        # --- Float ---
        mock_float_field = mock.Mock()
        mock_float_field.type = "float"

        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 500.0),
            "500",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 0.125),
            "0,125",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 1234.567),
            "1234,567",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 0.0),
            "0",
        )

        # --- Integer ---
        mock_integer_field = mock.Mock()
        mock_integer_field.type = "integer"
        self.assertEqual(
            mixin_instance._format_field_value(mock_integer_field, 123),
            "123",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_integer_field, 0),
            "",
        )

        # --- Test Char field formatting ---
        mock_char_field = mock.Mock()
        mock_char_field.type = "char"
        self.assertEqual(
            mixin_instance._format_field_value(
                mock_char_field,
                "Test String",
            ),
            "Test String",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_char_field, False),
            "",
        )

        # --- Test Date field formatting ---
        mock_date_field = mock.Mock()
        mock_date_field.type = "date"
        test_date = date(2023, 10, 26)
        self.assertEqual(
            mixin_instance._format_field_value(mock_date_field, test_date),
            "26102023",
        )
        self.assertEqual(mixin_instance._format_field_value(mock_date_field, None), "")

    def test_declaration_form_view(self):
        arch, _view = self.env["l10n_br_sped.fake.0000"]._get_view(view_type="form")
        arch = etree.tostring(arch, encoding="unicode")
        self.assertIn(  # some header button
            '<button name="button_done"',
            arch,
        )

        self.assertIn(  # some footer field
            '<field name="message_ids"',
            arch,
        )

        self.assertIn(  # simple SPED field
            '<field name="IND_SIT_ESP"',
            arch,
        )

    def test_declaration_buttons_are_translatable(self):
        """The header buttons are built in code: their labels must go through
        the translation function, or no .po file can ever translate them."""
        labels = {
            "button_populate_sped_from_odoo": "Pull Registers from Odoo",
            "button_flush_registers": "Flush Registers",
            "button_done": "Set to Done",
            "button_draft": "Reset to Draft",
            "button_create_sped_files": "Generate SPED File",
        }
        fake_pt_br = {label: f"{label} (pt)" for label in labels.values()}
        declaration_model = self.env["l10n_br_sped.fake.0000"]

        arch, _view = declaration_model._get_view(view_type="form")
        for name, label in labels.items():
            button = arch.xpath(f"//header/button[@name='{name}']")[0]
            self.assertEqual(button.get("string"), label)

        self.env["res.lang"]._activate_lang("pt_BR")
        with patch.object(
            code_translations, "get_python_translations", return_value=fake_pt_br
        ):
            arch, _view = declaration_model.with_context(lang="pt_BR")._get_view(
                view_type="form"
            )
        for name, label in labels.items():
            button = arch.xpath(f"//header/button[@name='{name}']")[0]
            self.assertEqual(button.get("string"), fake_pt_br[label])

    def test_declaration_children_separator_is_translated(self):
        """The title above each child registers list is built in code from the
        field label, which must come already translated."""
        self.env["res.lang"]._activate_lang("pt_BR")
        register_model = self.env["l10n_br_sped.fake.i010"]
        field = self.env["ir.model.fields"]._get(register_model._name, "reg_I050_ids")
        field.with_context(lang="pt_BR").field_description = "Plano de contas (pt)"

        arch, _view = register_model.with_context(lang="pt_BR")._get_view(
            view_type="form"
        )
        titles = arch.xpath("//separator/@string")
        self.assertIn("Plano de contas (pt)", titles)
        self.assertNotIn(register_model._fields["reg_I050_ids"].string, titles)

    def test_populate_and_split_attachment_creation(self):
        declaration = self.declaration
        self.assertEqual(declaration.state, "draft")

        ModelI010_proxy = self.env["l10n_br_sped.fake.i010"]
        ModelJ900_proxy = self.env["l10n_br_sped.fake.j900"]

        mock_i010_pull_func = mock.Mock()
        mock_j900_pull_func = mock.Mock()
        fake_top_register_proxies = [ModelI010_proxy, ModelJ900_proxy]

        with (
            patch.object(
                type(self.env["l10n_br_sped.mixin"]),
                "_get_top_registers",
                return_value=fake_top_register_proxies,
            ) as mock_get_top,
            patch.object(
                type(ModelI010_proxy),
                "_pull_records_from_odoo",
                side_effect=mock_i010_pull_func,
            ),
            patch.object(
                type(ModelJ900_proxy),
                "_pull_records_from_odoo",
                side_effect=mock_j900_pull_func,
            ),
        ):
            declaration.button_populate_sped_from_odoo()

            mock_get_top.assert_called_once_with("fake")

            mock_i010_pull_func.assert_called_once()
            args_i010_call = mock_i010_pull_func.call_args_list[0]
            self.assertEqual(args_i010_call.args[0], "fake")  # kind
            self.assertTrue(hasattr(args_i010_call.kwargs.get("log_msg"), "write"))

            mock_j900_pull_func.assert_called_once()
            args_j900_call = mock_j900_pull_func.call_args_list[0]
            self.assertEqual(args_j900_call.args[0], "fake")  # kind
            self.assertTrue(hasattr(args_j900_call.kwargs.get("log_msg"), "write"))

            # Chatter assertion
            self.assertTrue(
                declaration.message_ids, "No message posted after populating records."
            )
            last_message = declaration.message_ids[0]
            self.assertIn("Pulled from Odoo", last_message.body)

            # Mock _generate_sped_text
            simulated_sped_text_for_split = (
                "|0000|HEADER|...|\n"
                "|0001|OPEN_BLOCO_0|...|\n"
                "|I001|OPEN_BLOCO_I|...|\n"
                "|I010|DATA_BLOCO_I_LINE_1|...|\n"
                "|I012|DATA_BLOCO_I_LINE_2|...|\n"
                "|I015|DATA_BLOCO_I_LINE_3|...|\n"
                "|I990|CLOSE_BLOCO_I|...|\n"
                "|J001|OPEN_BLOCO_J|...|\n"
                "|J900|DATA_BLOCO_J_LINE_1|...|\n"
                "|J930|DATA_BLOCO_J_LINE_2|...|\n"
                "|J990|CLOSE_BLOCO_J|...|\n"
                "|C001|OPEN_BLOCO_C|...|\n"
                "|C040|DATA_BLOCO_C_LINE_1|...|\n"
                "|C050|DATA_BLOCO_C_LINE_2|...|\n"
                "|C100|DATA_BLOCO_C_LINE_3|...|\n"
                "|C990|CLOSE_BLOCO_C|...|\n"
                "|0990|CLOSE_BLOCO_0|...|\n"
                "|9001|OPEN_BLOCO_9|...|\n"
                "|9999|FOOTER|...|\n"
            )

            with patch.object(
                type(declaration),
                "_generate_sped_text",
                return_value=simulated_sped_text_for_split,
            ) as mock_generate:
                declaration.write({"split_sped_by_bloco": True, "state": "done"})
                declaration.button_create_sped_files()
                mock_generate.assert_called_once()

            attachments = self.env["ir.attachment"].search(
                [("res_model", "=", declaration._name), ("res_id", "=", declaration.id)]
            )

            self.assertEqual(
                len(attachments),
                3,
                f"Expected 3 attachments for data blocos I, J, C. "
                f"Got: {attachments.mapped('name')}",
            )

            decl_name_part = (
                f"{declaration.DT_FIN:%m-%Y}-"
                f"{declaration.company_id.name.replace(' ', '_')}"
            )

            # Check Bloco I
            att_i = attachments.filtered(
                lambda a: f"FAKE-bloco_I-{decl_name_part}.txt" in a.name
            )
            self.assertTrue(att_i, "Attachment for Bloco I not found.")
            content_i = base64.b64decode(att_i.datas).decode("utf-8").strip()
            expected_content_i_lines = [
                "|I001|OPEN_BLOCO_I|...|",
                "|I010|DATA_BLOCO_I_LINE_1|...|",
                "|I012|DATA_BLOCO_I_LINE_2|...|",
                "|I015|DATA_BLOCO_I_LINE_3|...|",
                "|I990|CLOSE_BLOCO_I|...|",
            ]
            self.assertEqual(content_i, "\r\n".join(expected_content_i_lines))

            # Check Bloco J
            att_j = attachments.filtered(
                lambda a: f"FAKE-bloco_J-{decl_name_part}.txt" in a.name
            )
            self.assertTrue(att_j, "Attachment for Bloco J not found.")
            content_j = base64.b64decode(att_j.datas).decode("utf-8").strip()
            expected_content_j_lines = [
                "|J001|OPEN_BLOCO_J|...|",
                "|J900|DATA_BLOCO_J_LINE_1|...|",
                "|J930|DATA_BLOCO_J_LINE_2|...|",
                "|J990|CLOSE_BLOCO_J|...|",
            ]
            self.assertEqual(content_j, "\r\n".join(expected_content_j_lines))

            # Check Bloco C
            att_c = attachments.filtered(
                lambda a: f"FAKE-bloco_C-{decl_name_part}.txt" in a.name
            )
            self.assertTrue(att_c, "Attachment for Bloco C not found.")
            content_c = base64.b64decode(att_c.datas).decode("utf-8").strip()
            expected_content_c_lines = [
                "|C001|OPEN_BLOCO_C|...|",
                "|C040|DATA_BLOCO_C_LINE_1|...|",
                "|C050|DATA_BLOCO_C_LINE_2|...|",
                "|C100|DATA_BLOCO_C_LINE_3|...|",
                "|C990|CLOSE_BLOCO_C|...|",
            ]
            self.assertEqual(content_c, "\r\n".join(expected_content_c_lines))

            # Test _create_sped_attachment directly
            single_attachment_val = declaration._create_sped_attachment(
                "SINGLE FILE CONTENT"
            )
            self.assertEqual(
                single_attachment_val["name"], f"FAKE-{decl_name_part}.txt"
            )

            bloco_attachment_val = declaration._create_sped_attachment(
                "BLOCO X CONTENT", bloco="X"
            )
            self.assertEqual(
                bloco_attachment_val["name"], f"FAKE-bloco_X-{decl_name_part}.txt"
            )
            declaration._compute_fiscal_documents()
            declaration.button_done()
            declaration.button_draft()
            declaration.button_flush_registers()

    def test_declaration_defaults_and_onchange_company(self):
        """
        Test default date methods and onchange_company_id for SpedDeclaration.
        """
        DeclarationModel = self.env[
            "l10n_br_sped.fake.0000"
        ]  # Using your fake 0000 model

        # 1. Test default date methods
        # Get today's date as Odoo would in fields.Date.context_today(self)
        today = fields.Date.context_today(
            DeclarationModel
        )  # Pass a model or record for context

        expected_dt_ini = today.replace(year=today.year - 1)
        expected_dt_fin = today.replace(year=today.year + 1)  # Your default is year + 1

        self.assertEqual(
            DeclarationModel._get_default_dt_ini(),
            expected_dt_ini,
            "Default DT_INI is not as expected.",
        )
        self.assertEqual(
            DeclarationModel._get_default_dt_fin(),
            expected_dt_fin,
            "Default DT_FIN is not as expected.",
        )

        # 2. Test declaration creation with defaults
        # We need a company for the default value of company_id
        # self.env.company is usually set in test environments
        self.assertTrue(self.env.company, "Default company not found for test.")

        new_declaration = DeclarationModel.create(
            {
                "TIP_ECD": "0",
                "LECD": "009",
                "NOME": "test",
                "CNPJ": "Z1234567",
                "UF": "SP",
                "IND_NIRE": "0",
                "IND_GRANDE_PORTE": "0",
                "IDENT_MF": "BRL",
                "IND_ESC_CONS": "S",
                "IND_CENTRALIZADA": "0",
                "IND_MUDANC_PC": "0",
            }
        )

        self.assertEqual(
            new_declaration.company_id,
            self.env.company,
            "Default company_id not set correctly.",
        )
        self.assertEqual(
            new_declaration.DT_INI,
            expected_dt_ini,
            "DT_INI on new record not set to default.",
        )
        self.assertEqual(
            new_declaration.DT_FIN,
            expected_dt_fin,  # Adjusted to year + 1 as per your code
            "DT_FIN on new record not set to default.",
        )
        self.assertEqual(
            new_declaration.state, "draft", "Default state is not 'draft'."
        )

        # 3. Test onchange_company_id
        declaration_for_onchange = DeclarationModel.new()

        # Store original values that might be changed by onchange
        original_nome = declaration_for_onchange.NOME

        # Mock _map_from_odoo to return some values
        # Note: _map_from_odoo is on the *concrete* class l10n_br_sped.fake.0000
        # The onchange calls self._map_from_odoo
        mocked_map_values = {
            "NOME": "Mapped Company Name",
            "CNPJ": "12345678000199",
        }

        with patch.object(
            type(declaration_for_onchange),
            "_map_from_odoo",
            return_value=mocked_map_values,
        ) as mock_map:
            # Trigger the onchange
            declaration_for_onchange.company_id = self.env.company  # Or another company
            declaration_for_onchange.onchange_company_id()

            # Assert _map_from_odoo was called
            mock_map.assert_called_once_with(self.env.company, None, None)

            # Assert that fields were updated based on mocked_map_values
            self.assertEqual(declaration_for_onchange.NOME, "Mapped Company Name")
            self.assertEqual(declaration_for_onchange.CNPJ, "12345678000199")
            # If NOME was previously set, ensure it changed
            self.assertNotEqual(
                original_nome, "Mapped Company Name", "NOME should have changed."
            )

        # Test onchange with no company_id (should simply return)
        declaration_no_company = DeclarationModel.new({"NOME": "Initial Name"})
        declaration_no_company.company_id = False  # Set to None/False
        # We don't need to mock _map_from_odoo here as it shouldn't be called
        with patch.object(
            type(declaration_no_company), "_map_from_odoo"
        ) as mock_map_no_company:
            res = declaration_no_company.onchange_company_id()
            self.assertIsNone(
                res, "onchange_company_id should return None if no company_id."
            )
            mock_map_no_company.assert_not_called()
            self.assertEqual(
                declaration_no_company.NOME,
                "Initial Name",
                "Fields should not change if company_id is False.",
            )

    def test_pull_records_from_odoo_logic(self):
        """
        Test the core logic of _pull_records_from_odoo for a sample register.
        We'll use l10n_br_sped.fake.0007 which doesn't have _odoo_model defined,
        so it will fall into the 'elif hasattr(self, "_map_from_odoo"):' block
        if we define _map_from_odoo on it for the test.

        If we want to test a register that *does* have _odoo_model,
        we'd need to create some res.partner records for example.
        Let's first test the case where _map_from_odoo is called directly.
        """
        declaration = self.declaration
        log_msg_container = StringIO()  # To pass to the method

        Reg0007Model = self.env["l10n_br_sped.fake.0007"]

        # Scenario 1: Register uses only _map_from_odoo (no _odoo_model or _odoo_query)
        # We need to make sure _map_from_odoo is defined on the test model.
        # Let's patch it for this test to control its return value.

        mapped_values_for_0007 = {
            "COD_ENT_REF": "01",  # Example value
            "COD_INSCR": "Z1234567",  # Example value
            "declaration_id": declaration.id,  # Should be set by _pull_records
        }

        # We are calling Reg0007Model._pull_records_from_odoo(...)
        with (
            patch.object(
                type(Reg0007Model),
                "_map_from_odoo",
                return_value=mapped_values_for_0007,
            ) as mock_map_0007,
            patch.object(
                type(Reg0007Model), "create", wraps=Reg0007Model.create
            ) as mock_create_0007,
        ):
            Reg0007Model.with_context(declaration=declaration)._pull_records_from_odoo(
                kind="fake", level=2, log_msg=log_msg_container
            )

            mock_map_0007.assert_called_once_with(None, None, declaration)

            # Assert 'create' was called with the mapped values
            mock_create_0007.assert_called_once()
            created_vals = mock_create_0007.call_args[0][0]
            self.assertEqual(
                created_vals.get("COD_ENT_REF"), mapped_values_for_0007["COD_ENT_REF"]
            )
            self.assertEqual(
                created_vals.get("COD_INSCR"), mapped_values_for_0007["COD_INSCR"]
            )
            self.assertEqual(created_vals.get("declaration_id"), declaration.id)

        # Check that one record was actually created
        created_0007_records = Reg0007Model.search(
            [("declaration_id", "=", declaration.id)]
        )
        self.assertEqual(len(created_0007_records), 2)
        self.assertEqual(created_0007_records[-1].COD_ENT_REF, "01")

        # Scenario 2: Register uses _odoo_model and _odoo_domain
        RegI010Model = self.env["l10n_br_sped.fake.i010"]

        # Create some dummy Odoo records that _odoo_domain would find
        # For this, we need a simple model to act as the source. Let's use 'res.partner'
        # and create a couple of partners.
        PartnerModel = self.env["res.partner"]
        partner1 = PartnerModel.create({"name": "Test Partner SPED 1"})
        partner2 = PartnerModel.create({"name": "Test Partner SPED 2"})

        # Define what _map_from_odoo for I010 should return for each partner
        def i010_map_side_effect(record, parent_record, decl, index=0):
            if record == partner1:
                return {"IND_ESC": "G", "COD_VER_LC": "9.00", "declaration_id": decl.id}
            if record == partner2:
                return {"IND_ESC": "R", "COD_VER_LC": "9.00", "declaration_id": decl.id}
            return {}

        # Temporarily set _odoo_model and mock _odoo_domain for RegI010Model
        # and mock its _map_from_odoo
        with (
            patch.object(type(RegI010Model), "_odoo_model", "res.partner"),
            patch.object(
                type(RegI010Model),
                "_odoo_domain",
                return_value=[("id", "in", [partner1.id, partner2.id])],
            ) as mock_domain_i010,
            patch.object(
                type(RegI010Model), "_map_from_odoo", side_effect=i010_map_side_effect
            ) as mock_map_i010,
            patch.object(
                type(RegI010Model), "create", wraps=RegI010Model.create
            ) as mock_create_i010,
        ):
            # Clear previous log_msg
            log_msg_container = StringIO()
            RegI010Model.with_context(declaration=declaration)._pull_records_from_odoo(
                kind="fake", level=2, log_msg=log_msg_container
            )

            mock_domain_i010.assert_called_once_with(None, declaration)
            self.assertEqual(
                mock_map_i010.call_count, 2
            )  # Called for partner1 and partner2

            # Check calls to _map_from_odoo
            mock_map_i010.assert_any_call(partner1, None, declaration, index=0)
            mock_map_i010.assert_any_call(partner2, None, declaration, index=1)

            # Check calls to create: the whole level is written in a single
            # batched call, so `create` receives one list with the vals of
            # every record, in the same order as the source records.
            self.assertEqual(mock_create_i010.call_count, 1)
            batch_vals = mock_create_i010.call_args_list[0][0][0]
            self.assertIsInstance(batch_vals, list)
            self.assertEqual(len(batch_vals), 2)
            created_vals_1, created_vals_2 = batch_vals

            self.assertEqual(created_vals_1.get("IND_ESC"), "G")
            self.assertEqual(created_vals_1.get("res_model"), "res.partner")
            self.assertEqual(created_vals_1.get("res_id"), partner1.id)

            self.assertEqual(created_vals_2.get("IND_ESC"), "R")
            self.assertEqual(created_vals_2.get("res_model"), "res.partner")
            self.assertEqual(created_vals_2.get("res_id"), partner2.id)

        created_i010_records = RegI010Model.search(
            [("declaration_id", "=", declaration.id)]
        )
        self.assertEqual(len(created_i010_records), 3)

    def test_compute_reference(self):
        """
        Test the _compute_reference method from SpedMixin.
        """
        FakeRegModel = self.env["l10n_br_sped.fake.0007"]

        # Scenario 1: res_model and res_id are set
        # Ensure the ir.model for 'res.partner' exists (it should by default in Odoo)
        partner_model = self.env["ir.model"].search(
            [("model", "=", "res.partner")], limit=1
        )
        self.assertTrue(
            partner_model,
            "ir.model for res.partner not found, test prerequisite missing.",
        )

        fake_reg_instance1 = FakeRegModel.create(
            {
                "res_model": "res.partner",
                "res_id": 123,
                "COD_ENT_REF": "01",
                "declaration_id": self.declaration.id,
            }
        )

        # Accessing the field triggers the compute method
        self.assertEqual(
            fake_reg_instance1.reference,
            "res.partner,123",
            "Reference string not computed as expected.",
        )

        # Scenario 2: res_model is not set
        fake_reg_instance2 = FakeRegModel.create(
            {
                "res_model": False,  # Explicitly set to False or None
                "res_id": 456,
                "COD_ENT_REF": "01",
                "declaration_id": self.declaration.id,
            }
        )
        self.assertEqual(
            fake_reg_instance2.reference,
            "",
            "Reference should be empty if res_model is not set.",
        )

        # Scenario 3: res_model is set but ir.model does not exist
        with self.assertRaisesRegex(
            UserError,
            "Undefined mapping model for Register l10n_br_sped.fake.0007 "
            "and model non.existent.model",
        ):
            fake_reg_instance3 = FakeRegModel.create(
                {
                    "res_model": "non.existent.model",
                    "res_id": 789,
                    "COD_ENT_REF": "01",
                    "declaration_id": self.declaration.id,
                }
            )
            _ = fake_reg_instance3.reference  # Trigger compute

        # Scenario 4: res_model is set, res_id is 0 or False
        fake_reg_instance4 = FakeRegModel.create(
            {
                "res_model": "res.partner",
                "res_id": 0,
                "COD_ENT_REF": "01",
                "declaration_id": self.declaration.id,
            }
        )
        self.assertEqual(
            fake_reg_instance4.reference,
            "res.partner,0",
            "Reference string not computed as expected for res_id=0.",
        )

    def test_attachment_is_encoded_in_latin1(self):
        """The SPED attachment is ISO-8859-1, not utf-8.

        The layout mandates Latin-1. With utf-8 every accented character
        takes two bytes and the government validator reads the text as
        mojibake: the ECF PVA shows "DISCRIMINA\u00c7\u00c3O" as
        "DISCRIMINA\u00c3\u0083O" and flags the whole line.
        """
        text = "|P200|1|DISCRIMINA\u00c7\u00c3O DA RECEITA BRUTA||\n"
        vals = self.declaration._create_sped_attachment(text)
        stored = base64.b64decode(vals["datas"])
        self.assertEqual(stored, text.replace("\n", "\r\n").encode("iso-8859-1"))
        # one byte per accented character, no utf-8 marker in the Latin range
        self.assertEqual(len(stored), len(text) + 1)
        self.assertNotIn(b"\xc3\x87", stored)

    def test_attachment_lines_end_in_crlf(self):
        """Every line, the last included, ends in CR LF: the layout says so and
        the PVA refuses a file with bare line feeds."""
        vals = self.declaration._create_sped_attachment("|0000|A|\n|0001|0|\n|9999|3|")
        stored = base64.b64decode(vals["datas"])
        self.assertEqual(stored, b"|0000|A|\r\n|0001|0|\r\n|9999|3|\r\n")
        self.assertNotIn(b"\n", stored.replace(b"\r\n", b""))

    def _generated_registers(self, declaration):
        """Count of the registers a pull created, by model."""
        counts = {}
        for name, model in self.env.registry.items():
            if (
                name.startswith("l10n_br_sped.fake.")
                and not model._abstract
                and "declaration_id" in model._fields
            ):
                counts[name] = self.env[name].search_count(
                    [
                        ("declaration_id", "=", declaration.id),
                        ("is_generated_from_odoo", "=", True),
                    ]
                )
        return counts

    def test_pulling_twice_does_not_duplicate(self):
        """A second pull replaces what the first one created and keeps what
        was typed by hand."""
        declaration = self.declaration
        typed = self.env["l10n_br_sped.fake.i010"].search(
            [("declaration_id", "=", declaration.id)], limit=1
        )
        self.assertTrue(typed, "the imported file has no I010")
        self.assertFalse(typed.is_generated_from_odoo)
        declaration.button_populate_sped_from_odoo()
        first = self._generated_registers(declaration)
        self.assertTrue(sum(first.values()), "the pull created no register")
        declaration.button_populate_sped_from_odoo()
        self.assertEqual(self._generated_registers(declaration), first)
        self.assertTrue(typed.exists())

    def _user_of(self, companies):
        # the fake register models have no access rule of their own
        self.env["ir.model.access"].create(
            {
                "name": "fake declaration: internal user",
                "model_id": self.env["ir.model"]._get_id("l10n_br_sped.fake.0000"),
                "group_id": self.env.ref("base.group_user").id,
                "perm_read": True,
            }
        )
        return self.env["res.users"].create(
            {
                "name": "SPED user of another company",
                "login": "sped_base_other_company",
                "email": "sped.other@example.com",
                "company_id": companies[0].id,
                "company_ids": [(6, 0, companies.ids)],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("l10n_br_fiscal.group_manager").id,
                        ],
                    )
                ],
            }
        )

    def test_declaration_runs_as_its_own_company(self):
        """The registers are pulled as the company of the declaration, even
        when another company is the active one of the session."""
        other = self.env["res.company"].create({"name": "Another company"})
        company = self.declaration.company_id
        user = self._user_of(other | company)
        declaration = self.declaration.with_user(user).with_context(
            allowed_company_ids=other.ids
        )
        in_company = declaration._in_company_context()
        self.assertEqual(in_company.env.company, company)
        self.assertEqual(in_company.env.companies, company)

    def test_user_without_the_company_gets_a_clear_error(self):
        other = self.env["res.company"].create({"name": "Another company"})
        user = self._user_of(other)
        declaration = self.declaration.with_user(user)
        with self.assertRaisesRegex(UserError, "no access to the company"):
            declaration._in_company_context()

    def test_character_outside_latin1_does_not_abort(self):
        """A symbol pasted in some label cannot block the whole file."""
        text = "|I250|Taxa \u20ac de servico|\n"
        vals = self.declaration._create_sped_attachment(text)
        stored = base64.b64decode(vals["datas"])
        self.assertEqual(len(stored), len(text) + 1)
        self.assertIn(b"?", stored)

    def test_import_reads_latin1(self):
        """Files received from third parties come in Latin-1 and must open."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".txt", delete=False
        ) as handle:
            with open(self.file_path, encoding="iso-8859-1") as original:
                content = original.read()
            handle.write(content.encode("iso-8859-1"))
            path = handle.name
        declaration = self.env["l10n_br_sped.mixin"]._import_file(path, "fake")
        self.assertTrue(declaration)

    def test_populate_fills_the_declaration_header(self):
        """The declaration IS the 0000: pulling must fill its own fields.

        Before the fix only the child registers were pulled and the header
        went out blank (LECD, the company identification), which the PVA
        refuses at the door. What the user typed must survive the pull.
        """
        company = self.declaration.company_id
        # the fake spec keeps Odoo required on the header fields, so the
        # create carries the minimum and the assertion targets the optional
        # mapped fields the pull must fill
        declaration = self.env["l10n_br_sped.fake.0000"].create(
            {
                "company_id": company.id,
                "DT_INI": "2019-01-01",
                "DT_FIN": "2019-12-31",
                "LECD": "LECD",
                "NOME": "typed by the user",
                "CNPJ": "00000000000000",
                "UF": "XX",
                "IND_NIRE": "0",
                "IND_FIN_ESC": "0",
                "IND_GRANDE_PORTE": "0",
                "TIP_ECD": 0,
                "IDENT_MF": "N",
                "IND_ESC_CONS": "N",
                "IND_CENTRALIZADA": "0",
                "IND_MUDANC_PC": "0",
            }
        )
        self.assertFalse(declaration.IE)
        declaration.button_populate_sped_from_odoo()
        # optional header fields came from the company mapping
        self.assertEqual(declaration.IE, misc.punctuation_rm(company.l10n_br_ie_code))
        self.assertEqual(declaration.COD_MUN, company.city_id.ibge_code)
        # what the user typed by hand is never overwritten
        self.assertEqual(declaration.NOME, "typed by the user")
        self.assertEqual(declaration.CNPJ, "00000000000000")

    def _fake_declaration(self, dt_ini, dt_fin):
        source = self.declaration
        return self.env["l10n_br_sped.fake.0000"].create(
            {
                "company_id": self.env.ref("l10n_br_base.empresa_lucro_presumido").id,
                "DT_INI": dt_ini,
                "DT_FIN": dt_fin,
                "LECD": source.LECD,
                "NOME": source.NOME,
                "CNPJ": source.CNPJ,
                "UF": source.UF,
                "IND_SIT_INI_PER": source.IND_SIT_INI_PER,
                "IND_NIRE": source.IND_NIRE,
                "IND_FIN_ESC": source.IND_FIN_ESC,
                "IND_GRANDE_PORTE": source.IND_GRANDE_PORTE,
                "TIP_ECD": source.TIP_ECD,
                "IDENT_MF": source.IDENT_MF,
                "IND_ESC_CONS": source.IND_ESC_CONS,
                "IND_CENTRALIZADA": source.IND_CENTRALIZADA,
                "IND_MUDANC_PC": source.IND_MUDANC_PC,
            }
        )

    def test_an_entry_is_in_the_period_it_came_in(self):
        """Emitted in June and received in July, an entry is in the July
        declaration; an outgoing document stays in the month of its emission,
        and an entry without entry date too."""
        june_emission = datetime(2026, 6, 28, 12, 0)
        july_entry = datetime(2026, 7, 3, 12, 0)
        entry = self._sped_document(
            901, document_date=june_emission, date_in_out=july_entry
        )
        out = self._sped_document(
            902,
            operation="fo_venda",
            document_date=june_emission,
            date_in_out=july_entry,
        )
        no_entry_date = self._sped_document(
            903, document_date=june_emission, date_in_out=False
        )
        june = self._fake_declaration("2026-06-01", "2026-06-30")
        july = self._fake_declaration("2026-07-01", "2026-07-31")
        self.assertIn(entry, july.fiscal_document_ids)
        self.assertNotIn(entry, june.fiscal_document_ids)
        self.assertIn(out, june.fiscal_document_ids)
        self.assertNotIn(out, july.fiscal_document_ids)
        self.assertIn(no_entry_date, june.fiscal_document_ids)

    def test_an_nfe_without_access_key_is_left_out_and_listed(self):
        """The C100 of an NF-e without a key goes out with an empty CHV_NFE and
        the PVA refuses the file: the document stays out of the declaration and
        the pull lists it in the history."""
        keyed = self._sped_document(911)
        keyless = self._sped_document(912, document_key=False)
        declaration = self._fake_declaration("2026-07-01", "2026-07-31")
        self.assertIn(keyed, declaration.fiscal_document_ids)
        self.assertNotIn(keyless, declaration.fiscal_document_ids)
        self.assertEqual(declaration._get_documents_without_access_key(), keyless)
        declaration.button_populate_sped_from_odoo()
        self.assertIn("1/912", " ".join(declaration.message_ids.mapped("body")))

    def test_the_pull_history_is_html_with_the_error_escaped(self):
        declaration = self._fake_declaration("2026-07-01", "2026-07-31")
        i010 = self.env["l10n_br_sped.fake.i010"]
        with (
            patch.object(
                type(self.env["l10n_br_sped.mixin"]),
                "_get_top_registers",
                return_value=[i010],
            ),
            patch.object(
                type(i010),
                "_pull_records_from_odoo",
                side_effect=ValueError("<b>broken</b>"),
            ),
            mute_logger("odoo.addons.l10n_br_sped_base.models.sped_declaration"),
        ):
            declaration.button_populate_sped_from_odoo()
        body = declaration.message_ids[0].body
        self.assertIn("<h3>", body)
        self.assertIn("<p", body)
        self.assertIn("&lt;b&gt;broken&lt;/b&gt;", body)

    def test_the_history_link_needs_no_access_to_the_actions(self):
        """A fiscal user cannot read the window actions: the link of the pull
        history to the registers must not need it."""
        action = self.env["ir.actions.act_window"].create(
            {"name": "Fake I010", "res_model": "l10n_br_sped.fake.i010"}
        )
        user = self._user_of(self.declaration.company_id)
        log_msg = StringIO()
        self.env["l10n_br_sped.fake.i010"].with_user(user)._log_chatter_sped_item(
            log_msg, 1
        )
        self.assertIn(f"/web#action={action.id}", log_msg.getvalue())

    def _attachments(self, declaration):
        return self.env["ir.attachment"].search(
            [("res_model", "=", declaration._name), ("res_id", "=", declaration.id)]
        )

    def test_the_file_is_made_of_the_registers_of_the_generation(self):
        """The registers are pulled again when the file is generated: a
        declaration never pulled still goes out with what Odoo has."""
        declaration = self._fake_declaration("2026-07-01", "2026-07-31")
        self.assertFalse(declaration.IE)
        declaration.button_create_sped_files()
        company = declaration.company_id
        self.assertEqual(declaration.IE, misc.punctuation_rm(company.l10n_br_ie_code))
        self.assertEqual(len(self._attachments(declaration)), 1)

    def test_a_register_that_cannot_be_pulled_stops_the_generation(self):
        declaration = self._fake_declaration("2026-07-01", "2026-07-31")
        i010 = self.env["l10n_br_sped.fake.i010"]
        with (
            patch.object(
                type(self.env["l10n_br_sped.mixin"]),
                "_get_top_registers",
                return_value=[i010],
            ),
            patch.object(
                type(i010),
                "_pull_records_from_odoo",
                side_effect=ValueError("broken mapping"),
            ),
            mute_logger("odoo.addons.l10n_br_sped_base.models.sped_declaration"),
        ):
            with self.assertRaisesRegex(UserError, "I010: broken mapping"):
                declaration.button_create_sped_files()
        self.assertFalse(self._attachments(declaration))

    def test_the_generation_says_what_the_accountant_lacks(self):
        declaration = self._fake_declaration("2026-07-01", "2026-07-31")
        company = declaration.company_id
        company.accountant_id = False
        with patch.object(
            type(declaration),
            "_get_accountant_required",
            return_value=[("crc_code", "CRC")],
        ):
            with self.assertRaisesRegex(UserError, "accountant of the company"):
                declaration.button_create_sped_files()
            company.accountant_id = self.env["res.partner"].create(
                {"name": "Accountant"}
            )
            with self.assertRaisesRegex(UserError, "lacks CRC"):
                declaration.button_create_sped_files()
            company.accountant_id.crc_code = "1SP123456/O-0"
            declaration.button_create_sped_files()
        self.assertEqual(len(self._attachments(declaration)), 1)

    def test_pull_skips_a_register_with_nothing_to_map(self):
        """A register without an Odoo record and without children is not
        created when its mapping comes back empty (a bare 0007 breaks the
        required fields of the layout): the pulled mark is not mapped data. With
        values it is created, and marked as pulled."""
        declaration = self.declaration
        reg_0007 = self.env["l10n_br_sped.fake.0007"].with_context(
            declaration=declaration
        )
        domain = [("declaration_id", "=", declaration.id)]
        before = reg_0007.search(domain)
        with (
            patch.object(type(reg_0007), "_map_from_odoo", return_value={}),
            patch.object(
                type(reg_0007), "create", wraps=reg_0007.create
            ) as create_0007,
        ):
            reg_0007._pull_records_from_odoo(kind="fake", level=2, log_msg=StringIO())
        create_0007.assert_not_called()

        values = {"COD_ENT_REF": "01", "declaration_id": declaration.id}
        with patch.object(type(reg_0007), "_map_from_odoo", return_value=values):
            reg_0007._pull_records_from_odoo(kind="fake", level=2, log_msg=StringIO())
        pulled = reg_0007.search(domain) - before
        self.assertEqual(len(pulled), 1)
        self.assertEqual(pulled.COD_ENT_REF, "01")
        self.assertTrue(pulled.is_generated_from_odoo)

    def test_a_register_the_layout_makes_in_the_pull_is_a_pulled_one(self):
        """A layout may create registers in its own code during the pull (the
        J050 of the ECF): they are pulled ones, so the next pull drops them
        instead of carrying them twice."""
        declaration = self.declaration
        i010 = self.env["l10n_br_sped.fake.i010"]
        domain = [("declaration_id", "=", declaration.id)]
        typed = i010.search(domain)

        def make_one(self_, kind, level, **kwargs):
            self_.create({"COD_VER_LC": "9.00", "declaration_id": declaration.id})

        with patch.object(
            type(i010), "_pull_records_from_odoo", autospec=True, side_effect=make_one
        ):
            declaration.button_populate_sped_from_odoo()
            declaration.button_populate_sped_from_odoo()
        pulled = i010.search(domain) - typed
        self.assertEqual(len(pulled), 1)
        self.assertTrue(pulled.is_generated_from_odoo)
        self.assertTrue(typed.exists())

    def test_a_register_pulls_records_built_in_python(self):
        """A register may build its records in Python (_odoo_records): each
        dict is mapped as a record and is the parent record of the registers
        below."""
        declaration = self.declaration
        reg_0007 = self.env["l10n_br_sped.fake.0007"].with_context(
            declaration=declaration
        )
        domain = [("declaration_id", "=", declaration.id)]
        before = reg_0007.search(domain)

        def map_record(self_, record, parent_record, declaration, index=0):
            return {"COD_ENT_REF": record["code"], "declaration_id": declaration.id}

        with (
            patch.object(
                type(reg_0007),
                "_odoo_records",
                create=True,
                return_value=[{"code": "01"}, {"code": "02"}],
            ) as odoo_records,
            patch.object(
                type(reg_0007), "_map_from_odoo", autospec=True, side_effect=map_record
            ),
        ):
            reg_0007._pull_records_from_odoo(kind="fake", level=2, log_msg=StringIO())
        odoo_records.assert_called_once_with(None, declaration)
        pulled = reg_0007.search(domain) - before
        self.assertEqual(sorted(pulled.mapped("COD_ENT_REF")), ["01", "02"])
        self.assertTrue(all(pulled.mapped("is_generated_from_odoo")))
