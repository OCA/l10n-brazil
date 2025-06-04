# Copyright 2024 Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from os import path

from odoo_test_helper import FakeModelLoader

from odoo.tests import SavepointCase

from odoo.addons import l10n_br_sped_base


class TestSpedBase(SavepointCase, FakeModelLoader):
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
        arch = self.env["l10n_br_sped.fake.i010"].fields_view_get(view_type="tree")[
            "arch"
        ]
        self.assertIn(  # link to declaration
            '<field name="declaration_id"',
            arch,
        )

        self.assertIn(  # simple SPED field
            '<field name="IND_ESC"',
            arch,
        )

    def test_register_form_view(self):
        arch = self.env["l10n_br_sped.fake.i010"].fields_view_get(view_type="form")[
            "arch"
        ]
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
        arch = self.env["l10n_br_sped.fake.0000"].fields_view_get(view_type="form")[
            "arch"
        ]
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
