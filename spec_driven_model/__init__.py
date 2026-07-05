import logging

from . import models


def install_same_label_filter():
    """Suppress 'Two fields ... have the same label' warnings from
    ir.model.fields._reflect_fields. Call this from any l10n_br module
    __init__.py to ensure the filter is active on every upgrade.

    Spec fields from NFe/CTe/MDFe schemas inherently share labels
    generated from their XSDs and cannot be changed at the source.
    """
    logger = logging.getLogger("odoo.addons.base.models.ir_model")

    # Check if our filter is already installed
    for f in logger.filters:
        if getattr(f, "name", None) == "spec_same_label":
            return

    class _SameLabelFilter(logging.Filter):
        name = "spec_same_label"

        def filter(self, record):
            msg = record.getMessage()
            if "Two fields" in msg and "have the same label" in msg:
                return False
            return True

    logger.addFilter(_SameLabelFilter())


# Install on first import (fresh install)
install_same_label_filter()
