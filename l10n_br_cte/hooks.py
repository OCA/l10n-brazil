# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import logging

import pkg_resources

# from nfelib.cte.bindings.v4_0.cte_tipos_basico_v4_00 import Tcte
from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo import SUPERUSER_ID, api
from odoo.exceptions import ValidationError

# pylint: disable=odoo-addons-relative-import
from odoo.addons import l10n_br_cte

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("select demo from ir_module_module where name='l10n_br_cte';")
    is_demo = cr.fetchone()[0]
    if is_demo:
        res_items = (
            "tests",
            "cte",
            "v4_00",
            "leiauteCTe",
            "CTe51160724686092000173570010000000031000000024.xml",
        )

        resource_path = "/".join(res_items)
        doc_stream = pkg_resources.resource_stream(l10n_br_cte.__name__, resource_path)
        binding = Tcte.from_xml(doc_stream.read().decode())
        document_number = binding.infCte.ide.nCT
        existing_docs = env["l10n_br_fiscal.document"].search(
            [("document_number", "=", document_number)]
        )
        try:
            existing_docs.unlink()
            cte = (
                env["cte.40.tcte_infcte"]
                .with_context(tracking_disable=True, edoc_type="in")
                .build_from_binding("cte", "40", binding.infCte)
            )
            _logger.info(cte.cte40_emit.cte40_CNPJ)
        except ValidationError:
            _logger.info(f"CTE-e already {document_number} imported by hooks")
