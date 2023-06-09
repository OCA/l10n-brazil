# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import _
from . import test_cnae
from . import test_service_type
from . import test_partner_profile
from . import test_ibpt_product
from . import test_ibpt_service
from . import test_fiscal_tax
from . import test_workflow
from . import test_fiscal_document_generic
from . import test_subsequent_operation
from . import test_uom_uom
from . import test_fiscal_document_nfse
from . import test_icms_regulation
from . import test_ncm

try:
    from erpbrasil.assinatura import certificado
    from . import test_certificate
except ModuleNotFoundError:
    _logger = logging.getLogger(__name__)
    _logger.error(
        _(
            "Python Library erpbrasil.assinatura not installed, "
            "test_certificate will be skipped."
            "You can install it later with: pip install erpbrasil.assinatura."
        )
    )
