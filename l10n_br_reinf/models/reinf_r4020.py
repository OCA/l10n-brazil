# Copyright 2026 KMEE - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
from collections import OrderedDict, defaultdict
from importlib import import_module

from odoo import _, models
from odoo.exceptions import UserError

from ..constants import (
    REINF_PROC_EMI,
    REINF_RECTIFY_ORIGINAL,
    REINF_VERSAO_PROCESSO,
)

_logger = logging.getLogger(__name__)

R4020_BINDING_MODULE = (
    "nfelib.reinf.bindings.v2_01_02.r_4020_evt4020_pagto_beneficiario_pj_v2_01_02"
)

# Limits of the layout. They are not advisory: the XSD refuses the event above
# them, so the generation splits instead of failing at the tax authority.
MAX_IDE_PGTO = 100
MAX_INFO_PGTO = 999

# tpInscEstab: 1 is a CNPJ. The establishment carries the FULL CNPJ of 14
# positions, while ideContri carries the root of 8. Two different rules in the
# same event, and mixing them up is a rejection.
TP_INSC_ESTAB_CNPJ = "1"

# Which field of the retencoes group each tax fills, as (base, value).
RETENTION_FIELDS = {
    "irpj": ("vlrBaseIR", "vlrIR"),
    "aggregated": ("vlrBaseAgreg", "vlrAgreg"),
    "csll": ("vlrBaseCSLL", "vlrCSLL"),
    "cofins": ("vlrBaseCofins", "vlrCofins"),
    "pis_pasep": ("vlrBasePP", "vlrPP"),
}


def reinf_amount(value):
    """Format an amount the way the layout wants it: comma as the separator."""
    return f"{value:.2f}".replace(".", ",")


class ReinfCalculationR4020(models.Model):
    """Generation of the R-4020 out of the calculation.

    The event is built DIRECTLY on the bindings, and not through a
    StackedModel, and the reason is structural: the R-4020 nests two levels of
    one2many (idePgto 1..100, each with infoPgto 1..999) and the StackedModel of
    spec_driven_model only flattens many2one. Mapping it would mean three extra
    concrete models holding a copy of what the calculation lines already say,
    kept in sync by hand. The calculation lines ARE the data; this only
    serializes them.

    What the event keeps is everything the event owns: its identifier, its
    state, its XML as an attachment and its receipt.
    """

    _inherit = "l10n_br_reinf.calculation"

    def _r4020_binding(self):
        """The Reinf root class of the R-4020 binding.

        Imported here, never at the loading of the addon, and before any use:
        the nfelib is an external dependency.
        """
        try:
            return import_module(R4020_BINDING_MODULE).Reinf
        except ImportError as error:
            raise UserError(
                _(
                    "The binding module %s is not available. Install a nfelib "
                    "with the EFD-Reinf bindings.",
                    R4020_BINDING_MODULE,
                )
            ) from error

    def _r4020_declarable_lines(self):
        """Lines that go into a R-4020 of this competence."""
        self.ensure_one()
        return self.line_ids.filtered(
            lambda line: line.state != "excluded" and line.partner_id
        )

    def _r4020_units(self, lines):
        """Split the lines of a beneficiary into idePgto units.

        A unit is one nature of income with at most MAX_INFO_PGTO payments. A
        nature with more than that becomes two units, which the caller may then
        place in two events.
        """
        by_nature = OrderedDict()
        for line in lines.sorted(
            lambda item: (item.nature_income_id.code or "", item.fg_date)
        ):
            by_nature.setdefault(line.nature_income_id, []).append(line)
        units = []
        for nature, nature_lines in by_nature.items():
            dates = OrderedDict()
            for line in nature_lines:
                dates.setdefault(line.fg_date, []).append(line)
            date_groups = list(dates.items())
            for start in range(0, len(date_groups), MAX_INFO_PGTO):
                units.append((nature, date_groups[start : start + MAX_INFO_PGTO]))
        return units

    def _r4020_retentions(self, binding, lines):
        """The retencoes group of one infoPgto.

        Two rules of the layout are enforced here, and both are about not
        creating debt that does not exist:

        * a withholding that was not suffered has its field ABSENT, never
          filled with 0,00. The layout asks for a value greater than zero, and
          a zero would be read as a declared withholding of zero;
        * the aggregated value and the separate values of CSLL, COFINS and
          PIS/PASEP are MUTUALLY EXCLUSIVE in the same idePgto. Sending both
          duplicates the debt in the DCTFWeb, so this refuses to serialize
          instead of shipping it.
        """
        values = {}
        for line in lines:
            fields_of_tax = RETENTION_FIELDS.get(line.tax)
            if not fields_of_tax:
                continue
            withheld = abs(line.wh_amount)
            if not withheld:
                continue
            base_field, value_field = fields_of_tax
            values[base_field] = reinf_amount(abs(line.base_amount))
            values[value_field] = reinf_amount(withheld)
        separate = {"vlrCSLL", "vlrCofins", "vlrPP"} & set(values)
        if "vlrAgreg" in values and separate:
            raise UserError(
                _(
                    "The aggregated withholding and the separate withholdings "
                    "of CSLL, COFINS and PIS/PASEP cannot travel in the same "
                    "payment: it duplicates the debt in the DCTFWeb. Found "
                    "together: %s.",
                    ", ".join(sorted(separate)),
                )
            )
        if not values:
            return None
        return binding.EvtRetPj.IdeEstab.IdeBenef.IdePgto.InfoPgto.Retencoes(**values)

    def _build_r4020_xml(self, event):
        """Serialize the R-4020 of one event, unsigned.

        The event says which beneficiary and which slice of the competence it
        declares: its own calculation lines.
        """
        self.ensure_one()
        binding = self._r4020_binding()
        evt = binding.EvtRetPj
        company = self.company_id
        partner = event.partner_id
        lines = event.calculation_line_ids
        if not lines:
            raise UserError(
                _(
                    "The event %s has no calculation line, so there is nothing "
                    "to declare.",
                    event.display_name,
                )
            )
        inscription_type, inscription = company._reinf_inscription()

        ide_pgto = []
        for nature, date_groups in self._r4020_units(lines):
            info_pgto = []
            for fg_date, date_lines in date_groups:
                retentions = self._r4020_retentions(binding, date_lines)
                info_pgto.append(
                    evt.IdeEstab.IdeBenef.IdePgto.InfoPgto(
                        dtFG=fields_date_str(fg_date),
                        vlrBruto=reinf_amount(
                            max(abs(line.base_amount) for line in date_lines)
                        ),
                        retencoes=retentions,
                    )
                )
            ide_pgto.append(
                evt.IdeEstab.IdeBenef.IdePgto(
                    natRend=nature.code,
                    infoPgto=info_pgto,
                )
            )

        ide_benef = evt.IdeEstab.IdeBenef(
            cnpjBenef=(partner.cnpj_cpf_stripped or "").upper(),
            nmBenef=(partner.legal_name or partner.name or "")[:70],
            ideEvtAdic=event.additional_event or None,
            idePgto=ide_pgto,
        )
        evt_binding = evt(
            id=event.event_key,
            ideEvento=evt.IdeEvento(
                indRetif=event.rectify_indicator or REINF_RECTIFY_ORIGINAL,
                nrRecibo=event.rectified_event_id.receipt_number or None,
                perApur=self.period,
                tpAmb=company._reinf_environment(),
                procEmi=REINF_PROC_EMI,
                verProc=REINF_VERSAO_PROCESSO,
            ),
            ideContri=evt.IdeContri(
                tpInsc=inscription_type,
                nrInsc=inscription,
            ),
            ideEstab=evt.IdeEstab(
                tpInscEstab=TP_INSC_ESTAB_CNPJ,
                nrInscEstab=(company.cnpj_cpf_stripped or "").upper(),
                ideBenef=ide_benef,
            ),
        )
        return binding(evtRetPJ=evt_binding, signature=None).to_xml()

    def _generate_r4020(self):
        """One R-4020 per beneficiary of the competence, split when needed.

        The split is not optional: above 100 idePgto or 999 infoPgto the XSD
        refuses the event, so the extra events are generated with ideEvtAdic,
        which is what ties them together for the tax authority.
        """
        self.ensure_one()
        event_model = self.env["l10n_br_reinf.event"]
        self.event_ids.filtered(
            lambda event: event.event_type == "R-4020"
            and event.state in ("draft", "validated")
        ).unlink()

        by_partner = defaultdict(lambda: self.env["l10n_br_reinf.calculation.line"])
        for line in self._r4020_declarable_lines():
            by_partner[line.partner_id] |= line

        events = event_model
        for partner, lines in by_partner.items():
            units = self._r4020_units(lines)
            for index, start in enumerate(range(0, len(units), MAX_IDE_PGTO)):
                chunk = units[start : start + MAX_IDE_PGTO]
                chunk_lines = self.env["l10n_br_reinf.calculation.line"]
                for _nature, date_groups in chunk:
                    for _fg_date, date_lines in date_groups:
                        for line in date_lines:
                            chunk_lines |= line
                event = event_model.create(
                    {
                        "company_id": self.company_id.id,
                        "event_type": "R-4020",
                        "period": self.period,
                        "partner_id": partner.id,
                        "calculation_id": self.id,
                        # The first event of a beneficiary has no ideEvtAdic;
                        # the following ones say which slice they are.
                        "additional_event": f"{index + 1:02d}" if index else False,
                        "origin_model": self._name,
                        "origin_id": self.id,
                        "origin": self.display_name,
                    }
                )
                chunk_lines.write({"event_id": event.id})
                event.action_validate()
                event.action_generate_xml()
                events |= event
        return events


def fields_date_str(value):
    """dtFG as the layout wants it, AAAA-MM-DD."""
    return value.strftime("%Y-%m-%d")
