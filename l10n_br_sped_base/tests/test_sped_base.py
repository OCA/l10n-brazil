# Copyright 2024 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import base64
from os import path
from unittest import mock
from unittest.mock import patch  # Ensure patch is from unittest.mock

from lxml import etree
from odoo_test_helper import FakeModelLoader

from odoo.tests import TransactionCase

from odoo.addons import l10n_br_sped_base


class TestSpedBase(TransactionCase, FakeModelLoader):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

        with patch.object(
            type(self.env["l10n_br_sped.mixin"]),
            "_get_top_registers",
            return_value=fake_top_register_proxies,
        ) as mock_get_top, patch.object(
            type(ModelI010_proxy),
            "_pull_records_from_odoo",
            side_effect=mock_i010_pull_func,
        ), patch.object(
            type(ModelJ900_proxy),
            "_pull_records_from_odoo",
            side_effect=mock_j900_pull_func,
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
