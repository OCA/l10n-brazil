# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

import nfelib
import pkg_resources
from nfelib.nfe.bindings.v4_0.leiaute_nfe_v4_00 import TnfeProc

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    if env.ref("base.module_l10n_br_nfe").demo:
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
            env["l10n_br_fiscal.document"].import_binding_nfe(
                binding, edoc_type="in", dry_run=False
            )
        except ValidationError:
            _logger.info(f"NF-e already {document_number} imported by hooks")
