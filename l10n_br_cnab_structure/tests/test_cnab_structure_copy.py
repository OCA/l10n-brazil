# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCNABStructureCopy(TransactionCase):
    def _check_copy(self, structure):
        new = structure.copy({"name": "Copy of %s" % structure.name})
        self.assertNotEqual(new, structure)
        for name in (
            "batch_ids",
            "line_ids",
            "cnab_payment_way_ids",
            "cnab_pix_key_type_ids",
            "cnab_pix_transfer_type_ids",
            "cnab_occurrence_ids",
            "cnab_payment_rule_ids",
        ):
            self.assertEqual(len(new[name]), len(structure[name]), name)
            self.assertFalse(new[name] & structure[name], name)
        self.assertEqual(
            len(new.line_ids.field_ids),
            len(structure.line_ids.field_ids),
        )
        self.assertEqual(
            len(new.line_ids.group_ids),
            len(structure.line_ids.group_ids),
        )
        self.assertEqual(
            len(new.line_ids.group_ids.condition_ids),
            len(structure.line_ids.group_ids.condition_ids),
        )
        # nothing in the copy may point back to the original structure
        self.assertFalse(new.batch_ids.line_ids.cnab_structure_id - new)
        self.assertFalse(new.line_ids.batch_id.cnab_structure_id - new)
        self.assertFalse(new.line_ids.cnab_payment_way_ids.cnab_structure_id - new)
        self.assertFalse(
            new.cnab_payment_rule_ids.payment_way_id & (structure.cnab_payment_way_ids)
        )
        self.assertFalse(new.cnab_payment_way_ids.batch_id & structure.batch_ids)
        self.assertFalse(
            new.line_ids.field_ids.cnab_group_id & (structure.line_ids.group_ids)
        )
        for field in new.line_ids.field_ids.filtered("cnab_group_id"):
            self.assertEqual(field.cnab_group_id.cnab_line_id, field.cnab_line_id)
        conditions = new.line_ids.group_ids.condition_ids
        self.assertFalse(
            conditions.field_id & structure.line_ids.field_ids,
        )
        return new

    def test_copy_itau_240(self):
        structure = self.env.ref("l10n_br_cnab_structure.cnab_itau_240")
        self.assertTrue(structure.line_ids.field_ids)
        self._check_copy(structure)

    def test_copy_bb_240(self):
        structure = self.env.ref("l10n_br_cnab_structure.cnab_bb_240")
        self.assertTrue(structure.batch_ids)
        self._check_copy(structure)
