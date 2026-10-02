# Copyright (C) 2019-2020 - Raphael Valyi Akretion
# Copyright 2024 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
import importlib.resources
import logging

from nfelib.cte.bindings.v4_0.cte_v4_00 import Tcte

from odoo.exceptions import ValidationError

# pylint: disable=odoo-addons-relative-import
from odoo.addons import l10n_br_cte

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    if env.ref("base.module_l10n_br_cte").demo:
        res_items = (
            "tests",
            "cte",
            "v4_00",
            "leiauteCTe",
            "CTe51160724686092000173570010000000031000000024.xml",
        )

        resource_path = "/".join(res_items)
        cte_stream = importlib.resources.files(l10n_br_cte.__name__).joinpath(
            resource_path
        )
        binding = Tcte.from_xml(cte_stream.read_text(encoding="utf-8"))
        document_number = binding.infCte.ide.nCT
        existing_docs = env["l10n_br_fiscal.document"].search(
            [("document_number", "=", document_number)]
        )
        try:
            existing_docs.unlink()
            env["l10n_br_fiscal.document"].import_binding_cte(
                binding, edoc_type="in", dry_run=False
            )
        except ValidationError:
            _logger.info(f"CTE-e already {document_number} imported by hooks")
