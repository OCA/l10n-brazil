from odoo.addons.spec_driven_model import install_same_label_filter

install_same_label_filter()

from .hooks import post_init_hook
from . import models
from . import report
from . import wizards
