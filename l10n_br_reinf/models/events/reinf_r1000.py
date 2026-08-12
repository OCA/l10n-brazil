# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from importlib import import_module

from odoo import _, api, fields
from odoo.exceptions import UserError

from odoo.addons.spec_driven_model.models import spec_models

from ...constants import REINF_PROC_EMI, REINF_VERSAO_PROCESSO

_logger = logging.getLogger(__name__)


class ReinfR1000(spec_models.StackedModel):
    """R-1000, the registration of the taxpayer.

    Why this is a model of its own instead of spec mixins injected into
    res.company, which is what the NF-e does with the emitter: the R-1000 is a
    VERSIONED declaration. It carries a validity period, it is amended by
    another R-1000 with novaValidade, and the XML of a past event has to stay
    reproducible. Fields living on res.company would only ever hold the
    current state, and the amendment of a closed period would be impossible.
    On top of that the root of the event, evtInfoContri, carries ideEvento
    (tpAmb, procEmi, verProc) and the id attribute, which are data of the
    event, not of the company.

    So the company holds the CONFIGURATION (classTrib, the indicators, who the
    contact is) and every event copies it at the moment it is built. The copy
    is deliberate: what was transmitted must not change when the company
    changes.
    """

    _name = "l10n_br_reinf.r1000"
    _inherit = ["reinf.21.evtinfocontri"]
    _description = "EFD-Reinf R-1000 Taxpayer Information"

    _reinf21_odoo_module = (
        "odoo.addons.l10n_br_reinf_spec.models.v2_01_02"
        ".r_1000_evt_info_contribuinte_v2_01_02"
    )
    _reinf21_binding_module = (
        "nfelib.reinf.bindings.v2_01_02.r_1000_evt_info_contribuinte_v2_01_02"
    )
    _reinf21_stacking_mixin = "reinf.21.evtinfocontri"
    # alteracao and exclusao are the other two branches of the choice of
    # infoContri, and each one repeats the whole idePeriodo / infoCadastro
    # structure. Stacking the three of them would make the branches share the
    # same columns and would make the export emit all of them at once, which
    # the choice of the XSD forbids. This phase declares the inclusao only.
    _reinf21_stacking_skip_paths = ("reinf21_alteracao", "reinf21_exclusao")

    event_id = fields.Many2one(
        comodel_name="l10n_br_reinf.event",
        required=True,
        ondelete="cascade",
        index=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        related="event_id.company_id",
        store=True,
        index=True,
    )

    @api.model
    def _prepare_from_company(self, company, event):
        """Build the values of a R-1000 out of the configuration of a company.

        Everything the layout asks for that is not a decision of the event
        itself comes from res.company, and is copied here.
        """
        company.ensure_one()
        inscription_type, inscription = company._reinf_inscription()
        contact = company.reinf_contact_id
        if not contact:
            raise UserError(
                _(
                    "The company %s has no EFD-Reinf contact. The R-1000 asks "
                    "for the name and the CPF of a person to be contacted.",
                    company.display_name,
                )
            )
        contact_cpf = "".join(filter(str.isdigit, contact.cnpj_cpf_stripped or ""))
        if len(contact_cpf) != 11:
            raise UserError(
                _(
                    "The EFD-Reinf contact %s must have a CPF with 11 digits.",
                    contact.display_name,
                )
            )
        if not company.reinf_class_trib:
            raise UserError(
                _(
                    "The company %s has no EFD-Reinf taxpayer classification "
                    "(classTrib).",
                    company.display_name,
                )
            )
        return {
            "event_id": event.id,
            "reinf21_id": event.event_key,
            # ideEvento
            "reinf21_tpAmb": company._reinf_environment(),
            "reinf21_procEmi": REINF_PROC_EMI,
            "reinf21_verProc": REINF_VERSAO_PROCESSO,
            # ideContri
            "reinf21_tpInsc": inscription_type,
            "reinf21_nrInsc": inscription,
            # infoContri / inclusao / idePeriodo
            "reinf21_iniValid": event.period,
            # infoContri / inclusao / infoCadastro
            "reinf21_classTrib": company.reinf_class_trib,
            "reinf21_indEscrituracao": "1" if company.reinf_ind_escrituracao else "0",
            "reinf21_indDesoneracao": "1" if company.reinf_ind_desoneracao else "0",
            "reinf21_indAcordoIsenMulta": (
                "1" if company.reinf_ind_acordo_isen_multa else "0"
            ),
            # infoCadastro / contato
            "reinf21_nmCtt": (contact.name or "")[:70],
            "reinf21_cpfCtt": contact_cpf,
            "reinf21_foneFixo": self._only_digits(contact.phone)[:13],
            "reinf21_foneCel": self._only_digits(contact.mobile)[:13],
            "reinf21_email": contact.email or "",
        }

    @api.model
    def _only_digits(self, value):
        return "".join(filter(str.isdigit, value or ""))

    @api.model
    def create_event(self, company, period):
        """Create the event and its R-1000, ready to be serialized."""
        event = self.env["l10n_br_reinf.event"].create(
            {
                "company_id": company.id,
                "event_type": "R-1000",
                "period": period,
                "origin_model": company._name,
                "origin_id": company.id,
                "origin": company.display_name,
            }
        )
        event.action_validate()
        r1000 = self.create(self._prepare_from_company(company, event))
        event.r1000_id = r1000
        return event

    def _binding_root_class(self):
        """The Reinf root class of the binding module of this event.

        Imported here, and never at the loading of the addon: the nfelib is an
        external dependency and a warning at load time turns the CI red.
        """
        self.ensure_one()
        module_name = self._get_spec_property("binding_module")
        try:
            module = import_module(module_name)
        except ImportError as error:
            raise UserError(
                _(
                    "The binding module %s is not available. Install a nfelib "
                    "with the EFD-Reinf bindings.",
                    module_name,
                )
            ) from error
        return module.Reinf

    def _build_event_xml(self):
        """Serialize the R-1000 as the XML of the event.

        The spec_driven_model walks the record and its stacked sub-records and
        builds the evtInfoContri binding; the root Reinf element only wraps it.
        The signature is not applied here: it belongs to the transmission,
        which is where the certificate is.
        """
        self.ensure_one()
        self.flush_recordset()
        # Resolved FIRST on purpose: _get_binding_class reads the binding out
        # of sys.modules without importing it, so it has to be imported before
        # the first _build_binding.
        root_class = self._binding_root_class()
        evt_binding = self._build_binding("reinf", "21")
        return root_class(evtInfoContri=evt_binding, signature=None).to_xml()
