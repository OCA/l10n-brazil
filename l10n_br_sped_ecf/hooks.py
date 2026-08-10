# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Importa a ECF de exemplo, para quem instala o modulo com dados demo.

    A importacao esta desligada porque o arquivo de exemplo atual nao e uma
    ECF valida: ele foi escrito a mao e a escrituracao nao o produziria. O
    exemplo passa a ser gerado pela propria escrituracao num PR seguinte, e
    ai a importacao volta.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_sped_ecf").demo:
        return
