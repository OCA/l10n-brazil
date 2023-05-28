# Copyright 2019 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from erpbrasil.base import misc

from odoo.tests import SavepointCase

from odoo.addons.l10n_br_fiscal.models.ibpt.taxes import (
    DeOlhoNoImposto,
    get_ibpt_product,
    get_ibpt_service,
)


class TestIbpt(SavepointCase):
    @classmethod
    def setUpClass(cls):

        super().setUpClass()
        cls.company = cls._create_compay()
        cls._switch_user_company(cls.env.user, cls.company)
        cls.product_tmpl_model = cls.env["product.template"]
        cls.tax_estimate_model = cls.env["l10n_br_fiscal.tax.estimate"]
        cls.ncm_model = cls.env["l10n_br_fiscal.ncm"]
        cls.nbs_model = cls.env["l10n_br_fiscal.nbs"]

    @classmethod
    def _switch_user_company(cls, user, company):
        """Add a company to the user's allowed & set to current."""
        user.write(
            {
                "company_ids": [(6, 0, (company + user.company_ids).ids)],
                "company_id": company.id,
            }
        )

    @classmethod
    def _check_ibpt_api(cls, company, ncm_nbs):
        """Check if IBPT API Webservice is online"""

        result = False
        try:
            config = DeOlhoNoImposto(
                company.ibpt_token,
                misc.punctuation_rm(company.cnpj_cpf),
                company.state_id.code,
            )
            if ncm_nbs._name == "l10n_br_fiscal.ncm":
                result = bool(get_ibpt_product(config, ncm_nbs.code_unmasked))

            if ncm_nbs._name == "l10n_br_fiscal.nbs":
                result = bool(get_ibpt_service(config, ncm_nbs.code_unmasked))
        except Exception:
            result = False
        return result

    @classmethod
    def _create_compay(cls):
        """Create and config Company to test IBPT API"""
        # Creating a company
        company = cls.env["res.company"].create(
            {
                "name": "Company Test Fiscal BR",
                "cnpj_cpf": "02.960.895/0002-12",
                "country_id": cls.env.ref("base.br").id,
                "state_id": cls.env.ref("base.state_br_es").id,
                "ibpt_api": True,
                "ibpt_update_days": 0,
                "ibpt_token": (
                    "dsaaodNP5i6RCu007nPQjiOPe5XIefnx"
                    "StS2PzOV3LlDRVNGdVJ5OOUlwWZhjFZk"
                ),
            }
        )

        if not cls._check_ibpt_api(company, cls.env.ref("l10n_br_fiscal.ncm_85030010")):
            company.write({"ibpt_api": False})

        return company

    @classmethod
    def _create_product_tmpl(cls, name, ncm):
        """Create products related with NCM"""

        product = cls.product_tmpl_model.create({"name": name, "ncm_id": ncm.id})
        return product

    @classmethod
    def _create_service_tmpl(cls, name, nbs):
        """Create services related with NBS"""

        product = cls.product_tmpl_model.create({"name": name, "nbs_id": nbs.id})
        return product
