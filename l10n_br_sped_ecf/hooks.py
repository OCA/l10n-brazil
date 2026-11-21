# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

from pathlib import Path

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Importa a ECF de exemplo, para quem instala o modulo com dados demo.

    O arquivo e gerado pela propria escrituracao (ver o teste
    ``test_gerar_arquivo_de_exemplo``), e nao escrito a mao: importa-lo aqui
    exercita o caminho de leitura logo na instalacao.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env.ref("base.module_l10n_br_sped_ecf").demo:
        caminho = Path(__file__).resolve().parent / "demo" / "demo_ecf.txt"
        env["l10n_br_sped.mixin"]._flush_registers("ecf")
        env["l10n_br_sped.mixin"]._import_file(caminho, "ecf")
