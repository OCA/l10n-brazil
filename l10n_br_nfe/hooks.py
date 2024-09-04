# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

from odoo.addons.spec_driven_model import hooks

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    hooks.register_hook(
        env, "l10n_br_nfe", "odoo.addons.l10n_br_nfe_spec.models.v4_0.leiaute_nfe_v4_00"
    )

    cr.execute("select demo from ir_module_module where name='l10n_br_nfe';")
    is_demo = cr.fetchone()[0]
    if is_demo:
        res_items = (
            "nfe",
            "samples",
            "v4_0",
            "leiauteNFe",
            "35180834128745000152550010000474491454651420-nfe.xml",
        )
        resource_path = "/".join(res_items)
        nfe_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = TnfeProc.from_xml(nfe_stream.read().decode())
        document_number = binding.NFe.infNFe.ide.nNF
        existing_nfes = env["l10n_br_fiscal.document"].search(
            [("document_number", "=", document_number)]
        )
        try:
            existing_nfes.unlink()
            nfe = (
                env["nfe.40.infnfe"]
                .with_context(tracking_disable=True, edoc_type="in")
                .build_from_binding(binding.NFe.infNFe)
            )
            _logger.info(nfe.nfe40_emit.nfe40_CNPJ)
        except ValidationError:
            _logger.info(f"NF-e already {document_number} imported by hooks")
