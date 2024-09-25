# @ 2020 KMEE INFORMATICA LTDA - www.kmee.com.br -
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
import os

from nfelib.mdfe.bindings.v3_0.proc_mdfe_v3_00 import MdfeProc

from odoo.models import NewId
from odoo.tests import SavepointCase

from odoo.addons import l10n_br_mdfe
from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)


class MDFeImportTest(SavepointCase):
    def test_import_in_mdfe_dry_run(self):
        binding = self._get_xml_binding()
        mdfe = (
            self.env["mdfe.30.tmdfe_infmdfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding(binding.infMDFe, dry_run=True)
        )
        assert isinstance(mdfe.id, NewId)
        self._check_mdfe(mdfe)

    def test_import_in_mdfe(self):
        binding = self._get_xml_binding()
        mdfe = (
            self.env["mdfe.30.tmdfe_infmdfe"]
            .with_context(tracking_disable=True, edoc_type="in")
            .build_from_binding(binding.infMDFe, dry_run=False)
        )

        assert isinstance(mdfe.id, int)
        self._check_mdfe(mdfe)

    def _get_xml_binding(self):
        hooks.register_hook(
            self.env,
            "l10n_br_mdfe",
            "odoo.addons.l10n_br_mdfe_spec.models.v3_0.mdfe_tipos_basico_v3_00",
        )
        xml_path = os.path.join(
            l10n_br_mdfe.__path__[0],
            "tests",
            "mdfe",
            "v3_00",
            "leiauteMDFe",
            "MDFe41190876676436000167580010000500001000437558.xml",
        )

        return MdfeProc.from_xml(open(xml_path).read())

    def _check_mdfe(self, mdfe):
        self.assertEqual(type(mdfe)._name, "l10n_br_fiscal.document")

        # ide
        self.assertEqual(mdfe.mdfe30_cMDF, "00043755")
        self.assertEqual(mdfe.mdfe30_infMunCarrega[0].mdfe30_xMunCarrega, "ARAUCARIA")
        self.assertEqual(mdfe.mdfe30_UFIni, "PR")
        self.assertEqual(mdfe.mdfe30_UFFim, "SC")

        # emit
        self.assertEqual(
            mdfe.company_id, self.env.ref("l10n_br_base.empresa_lucro_presumido")
        )

        # modal
        self.assertEqual(mdfe.mdfe30_RNTRC, "12345678")
        self.assertEqual(mdfe.mdfe30_cInt, "1")
        self.assertEqual(mdfe.mdfe30_placa, "AAA4444")
        self.assertEqual(mdfe.mdfe30_tara, "15000")
        self.assertEqual(
            mdfe.mdfe30_condutor[0].mdfe30_xNome, "MAURICIO ROBERTO MOLLER"
        )
        self.assertEqual(len(mdfe.mdfe30_veicReboque), 2)
