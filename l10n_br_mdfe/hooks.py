# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

import nfelib
import pkg_resources
from nfelib.mdfe.bindings.v3_0.mdfe_tipos_basico_v3_00 import Tmdfe

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_mdfe").demo:
        res_items = (
            "mdfe",
            "samples",
            "v3_0",
            "41190876676436000167580010000500001000437558-mdfe.xml",
        )
        resource_path = "/".join(res_items)
        doc_stream = pkg_resources.resource_stream(nfelib.__name__, resource_path)
        binding = Tmdfe.from_xml(doc_stream.read().decode())
        document_number = binding.infMDFe.ide.nMDF
        existing_docs = env["l10n_br_fiscal.document"].search(
            [("document_number", "=", document_number)]
        )
        try:
            existing_docs.unlink()
            env["l10n_br_fiscal.document"].import_binding_mdfe(
                binding, edoc_type="in", dry_run=False
            )
        except ValidationError:
            _logger.info(f"MDF-e already {document_number} imported by hooks")
