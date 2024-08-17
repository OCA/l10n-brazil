# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from . import test_account_move_sn
from . import test_account_move_lc
from . import test_account_taxes
from . import test_non_fiscal_move
from . import test_document_date
from . import test_invoice_refund
from . import test_move_discount

# FIXME: a few "AssertionError: field tax_ids is not visible"
# migration errors to fix!
from . import test_multi_localizations_invoice
