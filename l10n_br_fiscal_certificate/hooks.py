# Copyright (C) 2021 - Luis Felipe Mileo - KMEE
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from erpbrasil.assinatura import misc

from odoo import SUPERUSER_ID, _, api

from .constants import CERTIFICATE_TYPE_ECNPJ, CERTIFICATE_TYPE_NFE

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    def prepare_fake_certificate_vals(
        valid=True,
        passwd="123456",
        issuer="EMISSOR A TESTE",
        country="BR",
        subject="CERTIFICADO VALIDO TESTE",
        cert_type=CERTIFICATE_TYPE_NFE,
    ):
        return {
            "type": cert_type,
            "subtype": "a1",
            "password": passwd,
            "file": misc.create_fake_certificate_file(
                valid, passwd, issuer, country, subject
            ),
        }

    env.cr.execute(
        "select demo from ir_module_module where name='l10n_br_fiscal_certificate';"
    )
    if env.cr.fetchone()[0]:
        companies = [
            env.ref("base.main_company", raise_if_not_found=False),
            env.ref("l10n_br_base.empresa_lucro_presumido", raise_if_not_found=False),
            env.ref("l10n_br_base.empresa_simples_nacional", raise_if_not_found=False),
        ]
        try:
            for company in companies:
                l10n_br_fiscal_certificate_id = env["l10n_br_fiscal.certificate"]
                company.certificate_nfe_id = l10n_br_fiscal_certificate_id.create(
                    prepare_fake_certificate_vals()
                )
                company.certificate_ecnpj_id = l10n_br_fiscal_certificate_id.create(
                    prepare_fake_certificate_vals(cert_type=CERTIFICATE_TYPE_ECNPJ)
                )
        except NameError:  # (means from erpbrasil.assinatura import misc failed)
            _logger.error(
                _(
                    "Python Library erpbrasil.assinatura not installed!"
                    "You can install it later with: pip install erpbrasil.assinatura."
                    "Demo companies fake A1 certificates were not created."
                )
            )
