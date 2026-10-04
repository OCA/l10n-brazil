# Copyright (C) 2025 - TODAY - Raphael Valyi - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    module = env["ir.module.module"].search([("name", "=", "l10n_br_base")])
    if module.demo:
        for partner in env["res.partner"].search([("legal_name", "=", False)]):
            partner.legal_name = partner.name
        env.ref("l10n_br_base.res_partner_cliente2_sp_end_entrega").parent_id = env.ref(
            "l10n_br_base.res_partner_cliente2_sp"
        ).id
        env.ref(
            "l10n_br_base.res_partner_cliente7_rs_end_cobranca"
        ).parent_id = env.ref("l10n_br_base.res_partner_cliente7_rs").id
