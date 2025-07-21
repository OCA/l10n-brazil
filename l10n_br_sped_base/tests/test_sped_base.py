# Copyright 2024 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import base64
from datetime import date
from io import StringIO
from os import path
from unittest import mock
from unittest.mock import patch

from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase

from odoo.addons import l10n_br_sped_base


class TestSpedBase(TransactionCase, FakeModelLoader):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

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
        demo_path = path.join(l10n_br_sped_base.__path__[0], "tests")
        cls.file_path = path.join(demo_path, "demo_fake.txt")
        sped_mixin = cls.env["l10n_br_sped.mixin"]
        sped_mixin._flush_registers("fake")
        cls.declaration = sped_mixin._import_file(cls.file_path, "fake")

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_generate_sped(self):
        sped = self.declaration._generate_sped_text()
        with open(self.file_path) as f:
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

    def test_format_field_value(self):
        """
        Test the _format_field_value method from SpedMixin,
        focusing on Float and Monetary types.
        """
        mixin_instance = self.env["l10n_br_sped.fake.9.0000"]

        # --- Test Float field formatting ---
        mock_float_field = mock.Mock()
        mock_float_field.type = "float"
        mock_float_field.sped_decimals = 2  # Simulate the attribute you might add

        # Test float with 2 decimals
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 1234.567),
            "1234,567",
        )
        # Test float that results in integer after rounding
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 1234.001),
            "1234,001",
        )
        # Test zero float
        self.assertEqual(
            mixin_instance._format_field_value(mock_float_field, 0.0),
            "0",
        )

        # --- Test Monetary field formatting ---
        mock_monetary_field = mock.Mock()
        mock_monetary_field.type = "monetary"

        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 789.123),
            "789.123",
        )
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 789.00),
            "789",
        )
        # Test zero monetary
        self.assertEqual(
            mixin_instance._format_field_value(mock_monetary_field, 0.0),
            "",  # Your current logic returns "" for zero
        )

        # --- Test Integer field formatting ---
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
            self.assertEqual(content_i, "\n".join(expected_content_i_lines))

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
            self.assertEqual(content_j, "\n".join(expected_content_j_lines))

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
            self.assertEqual(content_c, "\n".join(expected_content_c_lines))

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

            # Check calls to create
            self.assertEqual(mock_create_i010.call_count, 2)
            created_vals_1 = mock_create_i010.call_args_list[0][0][
                0
            ]  # First call, first arg, vals dict
            created_vals_2 = mock_create_i010.call_args_list[1][0][
                0
            ]  # Second call, first arg, vals dict

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
