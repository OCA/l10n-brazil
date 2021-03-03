# Copyright 2021 Akretion (Raphaël Valyi <raphael.valyi@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import SavepointCase


class NFeStructure(SavepointCase):

    def test_inherited_fields(self):
        assert 'nfe40_CNPJ' in self.env['res.company']._fields.keys()

    def test_concrete_spec(self):
        # this ensure basic SQL is set up
        self.assertEqual(len(self.env['nfe.40.vol'].search(
            [('nfe40_marca', '=', 'NO_RECORD')])),
            0
        )

    def test_m2o_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env['nfe.40.lacres']._fields['nfe40_lacres_vol_id'].comodel_name,
            'nfe.40.vol'
        )

    def test_o2m_concrete_to_concrete_spec(self):
        self.assertEqual(
            self.env['nfe.40.vol']._fields['nfe40_lacres'].comodel_name,
            'nfe.40.lacres'
        )
        self.assertEqual(len(self.env['nfe.40.lacres'].search([
            ('nfe40_nLacre', '=', 'NO_RECORD')])),
            0
        )

    def test_m2o_stacked_to_odoo(self):
        self.assertEqual(
            self.env['l10n_br_fiscal.document']._fields['nfe40_dest'].comodel_name,
            'res.partner'
        )
        self.assertEqual(
            self.env['l10n_br_fiscal.document']._fields[
                'nfe40_infRespTec'].comodel_name,
            'res.partner'
        )

    def test_o2m_to_odoo(self):
        pass  # any such example?

    def test_m2o_stacked_to_concrete(self):
        # not stacked because optional
        avulsa_model = self.env['l10n_br_fiscal.document']._fields[
            'nfe40_avulsa'].comodel_name
        self.assertEqual(avulsa_model, 'nfe.40.avulsa')

    def test_m2o_stacked(self):
        # not stacked because optional
        nfe_model = self.env['l10n_br_fiscal.document']
        assert 'nfe40_ide' not in nfe_model._fields.keys()
        assert 'nfe40_imposto' not in nfe_model._fields.keys()

    def test_doc_stacking_points(self):
        doc_keys = ['nfe40_ICMSTot', 'nfe40_ISSQNtot', 'nfe40_ide',
                    'nfe40_pag', 'nfe40_retTrib', 'nfe40_total',
                    'nfe40_transp']
        keys = [k for k in
                self.env['l10n_br_fiscal.document']._stacking_points.keys()]
        self.assertEqual(sorted(keys), doc_keys)

    def test_doc_line_stacking_points(self):
        line_keys = ['nfe40_COFINS', 'nfe40_COFINSAliq', 'nfe40_COFINSNT',
                     'nfe40_COFINSOutr', 'nfe40_COFINSQtde', 'nfe40_COFINSST',
                     'nfe40_ICMS', 'nfe40_ICMSPart', 'nfe40_ICMSST',
                     'nfe40_ICMSUFDest', 'nfe40_II', 'nfe40_IPI',
                     'nfe40_IPINT', 'nfe40_IPITrib', 'nfe40_ISSQN',
                     'nfe40_PIS', 'nfe40_PISAliq', 'nfe40_PISNT',
                     'nfe40_PISOutr', 'nfe40_PISQtde', 'nfe40_PISST',
                     'nfe40_comb', 'nfe40_imposto', 'nfe40_med', 'nfe40_prod',
                     'nfe40_veicProd']
        keys = [k for k in
                self.env['l10n_br_fiscal.document.line']._stacking_points.keys()]
        self.assertEqual(sorted(keys), line_keys)

    def test_m2o_force_stack(self):
        pass

    def test_doc_visit_stack(self):
        pass

    def test_doc_line_visit_stack(self):
        pass
