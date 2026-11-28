# Copyright 2026 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove every non-alphanumeric character from Brazilian partner vat values.

    ``vat`` used to be normalized with ``punctuation_rm``, which keeps spaces,
    en dashes and zero-width spaces, so records created before this fix may
    still hold them. They break the NF-e export, which reads the raw ``vat``,
    and escape the duplicate CNPJ/CPF check, which compares ``vat`` with ``=``.
    """
    cr.execute(
        """
        UPDATE res_partner
        SET vat = regexp_replace(vat, '[^0-9A-Za-z]', '', 'g')
        WHERE country_id IN (SELECT id FROM res_country WHERE code = 'BR')
          AND vat ~ '[^0-9A-Za-z]'
        """
    )
    _logger.info("Removed non-alphanumeric characters from %s vat(s)", cr.rowcount)
