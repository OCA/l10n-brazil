# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""IBS/CBS calculation engine.

The rules are not hardcoded: each tax treatment carries the official
expressions of the Receita Federal Calculadora de Tributos, evaluated here
with Decimal arithmetic and the same rounding as the official engine
(HALF_EVEN, 8 decimals internally, 2 decimals on output).

Sequence, as in ``CalculoCbsIbsService``::

    aliquota         = nominal rate (input of the operation) / 100
    aliquotaEfetiva  = aliquota * (1 - percentualReducao)
                       * (1 - pRedutorCompraGov/100)
    baseCalculo      = baseCalculoInformada - impostoSeletivoInformado
                       + impostoSeletivoCalculado
    tributoCalculado = baseCalculo * aliquotaEfetiva
    tributoDevido    = tributoCalculado - valorDiferimento

The nominal rate is an input, never a property of the cClassTrib: the CBS rate
is set by the Senate from 2027 and each State/Municipality sets its IBS rate
from 2029.  ``l10n_br_fiscal.rtc.rate`` holds the table, ``rates`` overrides it
for a simulation.
"""

import ast
import re
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from odoo import api, fields, models

INTERNAL_PRECISION = Decimal("0.00000001")
MONEY_PRECISION = Decimal("0.01")
HUNDRED = Decimal("100")

IBS_CBS_TAXES = ("cbs", "ibs_uf", "ibs_mun")

_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Name,
    ast.Load,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.USub,
    ast.UAdd,
)


class RtcExpressionError(Exception):
    """Raised when an official expression cannot be evaluated."""


class RtcEngine(models.AbstractModel):
    _name = "l10n_br_fiscal.rtc.engine"
    _description = "RTC IBS/CBS calculation engine"

    # ------------------------------------------------------------------
    # rounding and expression evaluation
    # ------------------------------------------------------------------
    @api.model
    def _r8(self, value):
        """Internal rounding: 8 decimals, HALF_EVEN (banker's rounding)."""
        with localcontext() as context:
            context.prec = 40
            return value.quantize(INTERNAL_PRECISION, rounding=ROUND_HALF_EVEN)

    @api.model
    def _r2(self, value):
        with localcontext() as context:
            context.prec = 40
            return value.quantize(MONEY_PRECISION, rounding=ROUND_HALF_EVEN)

    @api.model
    def _to_decimal(self, value):
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value or 0))

    @api.model
    def _money(self, value):
        return float(self._r2(value))

    @api.model
    def _percent(self, value):
        """Fraction -> percent, 4 decimals, for reporting."""
        with localcontext() as context:
            context.prec = 40
            return float(
                (value * HUNDRED).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
            )

    @api.model
    def _parse_expression(self, expression):
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as error:
            raise RtcExpressionError(
                f"invalid expression {expression!r}: {error}"
            ) from error
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED_NODES):
                raise RtcExpressionError(
                    f"unsupported construct {type(node).__name__} " f"in {expression!r}"
                )
        return tree

    @api.model
    def _eval_node(self, node, variables):
        if isinstance(node, ast.Expression):
            return self._eval_node(node.body, variables)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int | float):
                return Decimal(str(node.value))
            raise RtcExpressionError(f"unsupported constant {node.value!r}")
        if isinstance(node, ast.Name):
            if node.id not in variables:
                raise RtcExpressionError(f"undefined variable {node.id!r}")
            return self._to_decimal(variables[node.id])
        if isinstance(node, ast.UnaryOp):
            value = self._eval_node(node.operand, variables)
            if isinstance(node.op, ast.USub):
                return -value
            return value
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, variables)
            right = self._eval_node(node.right, variables)
            if isinstance(node.op, ast.Add):
                return self._r8(left + right)
            if isinstance(node.op, ast.Sub):
                return self._r8(left - right)
            if isinstance(node.op, ast.Mult):
                return self._r8(left * right)
            if isinstance(node.op, ast.Div):
                if not right:
                    raise RtcExpressionError("division by zero")
                return self._r8(left / right)
        raise RtcExpressionError(f"unsupported node {type(node).__name__}")

    @api.model
    def _evaluate(self, expression, variables):
        if not expression:
            return Decimal("0")
        return self._eval_node(self._parse_expression(expression), variables)

    # ------------------------------------------------------------------
    # data lookups
    # ------------------------------------------------------------------
    @api.model
    def _classification(self, code, date):
        return self.env["l10n_br_fiscal.tax.classification"].search(
            [
                ("code", "=", code),
                ("date_start", "<=", date),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", date),
            ],
            limit=1,
        )

    @api.model
    def _nominal_rate(self, tax, date, state, city, rates):
        if rates and rates.get(tax) is not None:
            return self._to_decimal(rates[tax])
        return self.env["l10n_br_fiscal.rtc.rate"].get_rate(
            tax, date, state=state, city=city
        )

    @api.model
    def _check_nomenclature(self, classification, code, date):
        """Return None when the NCM/NBS fits the cClassTrib, else a message."""
        expected = classification.rtc_nomenclature
        if not code or expected in (False, "none"):
            return None
        allowed = {
            "ncm": ("ncm",),
            "nbs": ("nbs",),
            "nbs_ncm": ("nbs", "ncm"),
        }.get(expected, ())
        nomenclature = self.env["l10n_br_fiscal.rtc.nomenclature"]
        for nomenclature_type in allowed:
            if nomenclature.is_applicable(
                classification.code, code, nomenclature_type, date
            ):
                return None
        return (
            f"code {code} is not linked to cClassTrib {classification.code} "
            f"(expected {expected})"
        )

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    @api.model
    def _empty_result(self, cclass):
        return {
            "cclass": cclass,
            "status": "calculated",
            "errors": [],
            "taxes": {},
            "base": 0.0,
            "ibs": 0.0,
            "total": 0.0,
            "memoria": "",
            "legal_basis": "",
        }

    @api.model
    def _fail(self, result, code, message, status="error"):
        result["status"] = status
        result["errors"].append({"code": code, "message": message})
        return result

    @api.model
    def compute_item(
        self,
        cclass,
        base,
        date=None,
        state=None,
        city=None,
        is_informed=0.0,
        is_calculated=0.0,
        quantity=1.0,
        nomenclature_code=None,
        rates=None,
        gov_reducer=0.0,
    ):
        """Compute IBS/CBS for one document line.

        :param cclass: cClassTrib code (``200003``)
        :param base: ``baseCalculoInformada`` (base of the operation)
        :param date: tax fact date, defaults to today
        :param state: ``res.country.state`` record for the IBS state rate
        :param city: ``res.city`` record for the IBS municipal rate
        :param is_informed: ``impostoSeletivoInformado``
        :param is_calculated: ``impostoSeletivoCalculado``
        :param quantity: quantity, used by the ad rem / monophase treatments
        :param nomenclature_code: NCM or NBS of the product, for validation
        :param rates: nominal rates in percent, e.g. ``{"cbs": 8.8}``; the
            table ``l10n_br_fiscal.rtc.rate`` is used for the missing ones
        :param gov_reducer: ``pRedutorCompraGov`` in percentage points

        A rate missing from the official table is reported on the result
        (``RTC-007``) instead of raising: the line of a document keeps its
        legacy values when the Senate or the CGIBS has not published the
        rates of the year yet.
        """
        result = self._empty_result(cclass)
        date = fields.Date.to_date(date) or fields.Date.context_today(self)

        classification = self._classification(cclass, date)
        if not classification:
            return self._fail(
                result, "RTC-001", f"unknown cClassTrib {cclass} at {date}"
            )
        treatment = classification.rtc_treatment_id
        if not treatment:
            return self._fail(
                result, "RTC-002", f"cClassTrib {cclass} has no RTC treatment"
            )
        if treatment.code in (1, 2):
            return self._fail(
                result,
                "RTC-003",
                f"cClassTrib {cclass} is an Imposto Seletivo classification",
                status="not_applicable",
            )
        if treatment.has_adjustment:
            return self._fail(
                result,
                "RTC-004",
                f"treatment {treatment.code} ({treatment.name}) "
                "is not implemented yet",
                status="not_implemented",
            )

        mismatch = self._check_nomenclature(classification, nomenclature_code, date)
        if mismatch:
            return self._fail(result, "RTC-011", mismatch)

        result["legal_basis"] = classification.rtc_legal_basis_id.name or ""

        base_decimal = self._to_decimal(base)
        variables = {
            "baseCalculoInformada": base_decimal,
            "impostoSeletivoInformado": self._to_decimal(is_informed),
            "impostoSeletivoCalculado": self._to_decimal(is_calculated),
            "quantidade": self._to_decimal(quantity),
            "percentualReducao": Decimal("0"),
            "pRedutorCompraGov": self._to_decimal(gov_reducer),
            "aliquota": Decimal("0"),
            "aliquotaEfetiva": Decimal("0"),
            "tributoCalculado": Decimal("0"),
            "percentualDiferimento": Decimal("0"),
        }

        try:
            computed_base = self._evaluate(treatment.expr_base, variables)
            if computed_base < 0:
                computed_base = Decimal("0")
            variables["baseCalculo"] = computed_base

            memoria = []
            for tax in IBS_CBS_TAXES:
                try:
                    nominal = self._nominal_rate(tax, date, state, city, rates)
                except ValueError as error:
                    # A rate not published yet (2027+ until the Senate and
                    # the CGIBS vote it) is a data gap, not a bug: report it
                    # on the result so the line keeps the legacy values.
                    return self._fail(result, "RTC-007", str(error))
                reduction = self._to_decimal(classification._rtc_reduction(tax))
                variables["aliquota"] = self._r8(nominal / HUNDRED)
                variables["percentualReducao"] = self._r8(reduction / HUNDRED)

                # An informed nominal rate prevails over a literal expression
                # such as "0" or "2.08 / 100" (CalculoCbsIbsService rule); an
                # expression referring to ``aliquota`` is always evaluated.
                informed = bool(rates and rates.get(tax) is not None)
                if informed and not re.search(
                    r"\baliquota\b", treatment.expr_rate or ""
                ):
                    rate = self._r8(nominal / HUNDRED)
                else:
                    rate = self._evaluate(treatment.expr_rate, variables)
                variables["aliquota"] = rate
                effective = self._evaluate(treatment.expr_effective_rate, variables)
                variables["aliquotaEfetiva"] = effective
                variables["baseCalculo"] = computed_base
                computed = self._evaluate(treatment.expr_tax_computed, variables)
                variables["tributoCalculado"] = computed
                due = self._evaluate(treatment.expr_tax_due, variables)

                deferral_percent = Decimal("0")
                deferral_value = Decimal("0")
                if treatment.expr_deferral_percent:
                    variables["tributoCalculado"] = computed
                    deferral_percent = self._evaluate(
                        treatment.expr_deferral_percent, variables
                    )
                    variables["percentualDiferimento"] = deferral_percent
                    deferral_value = self._evaluate(
                        treatment.expr_deferral_value, variables
                    )
                    # Only the full deferral (100%) is in force.  Upstream
                    # subtracts the deferred value from both ``computed`` and
                    # ``due``; with 100% both formulas land on zero, but with a
                    # partial deferral they diverge (upstream subtracts twice).
                    # Rather than guessing, refuse the partial case.
                    if deferral_percent not in (Decimal("0"), Decimal("1")):
                        return self._fail(
                            result,
                            "RTC-006",
                            f"partial deferral ({deferral_percent}) is not "
                            f"implemented for treatment {treatment.code}",
                            status="not_implemented",
                        )
                    computed = max(computed - deferral_value, Decimal("0"))
                    due = max(due - deferral_value, Decimal("0"))

                result["taxes"][tax] = {
                    "rate": float(nominal),
                    "reduction": float(reduction),
                    "effective_rate": self._percent(effective),
                    "value": self._money(computed),
                    "due": self._money(due),
                    "deferral_percent": self._percent(deferral_percent),
                    "deferral_value": self._money(deferral_value),
                }
                memoria.append(
                    f"{tax.upper()} {float(nominal):.2f}% -{float(reduction):.2f}%"
                    f" = {self._percent(effective):.4f}% -> {self._money(computed):.2f}"
                )
        except RtcExpressionError as error:
            return self._fail(
                result,
                "RTC-005",
                f"treatment {treatment.code} cannot be evaluated: {error}",
                status="not_implemented",
            )

        result["base"] = self._money(computed_base)
        result["ibs"] = self._money(
            self._to_decimal(result["taxes"]["ibs_uf"]["value"])
            + self._to_decimal(result["taxes"]["ibs_mun"]["value"])
        )
        result["total"] = self._money(
            self._to_decimal(result["taxes"]["cbs"]["value"])
            + self._to_decimal(result["ibs"])
        )
        result["memoria"] = " | ".join(memoria)
        result["credit"] = {
            "cbs": classification.rtc_credit_acquirer_cbs,
            "ibs": classification.rtc_credit_acquirer_ibs,
            "prior_operation": classification.rtc_prior_credit or "",
        }
        return result

    @api.model
    def compute(self, items, **kwargs):
        """Compute a whole document. Returns per-item results and totals.

        ``items`` is a list of dicts accepted by :meth:`compute_item`, the key
        ``cclass`` (or ``cClassTrib``) being mandatory.
        """
        allowed_keys = {
            "cclass",
            "base",
            "date",
            "state",
            "city",
            "is_informed",
            "is_calculated",
            "quantity",
            "nomenclature_code",
            "rates",
            "gov_reducer",
        }
        results = []
        totals = {
            "base": 0.0,
            "cbs": 0.0,
            "ibs_uf": 0.0,
            "ibs_mun": 0.0,
            "ibs": 0.0,
            "total": 0.0,
        }
        for item in items:
            values = {key: value for key, value in item.items() if key in allowed_keys}
            values["cclass"] = item.get("cclass") or item.get("cClassTrib")
            result = self.compute_item(**values, **kwargs)
            results.append(result)
            if result["status"] != "calculated":
                continue
            totals["base"] += result["base"]
            for tax in IBS_CBS_TAXES:
                totals[tax] += result["taxes"][tax]["value"]
            totals["ibs"] += result["ibs"]
            totals["total"] += result["total"]

        for key in totals:
            totals[key] = self._money(self._to_decimal(totals[key]))
        return {"items": results, "totals": totals}

    # ------------------------------------------------------------------
    # Simples Nacional
    # ------------------------------------------------------------------
    @api.model
    def _sn_destination(self, destination, due, pending):
        """Apply the apuration matrix: DEVIDO, PENDENTE_SUSPENSO or ZERO."""
        if destination == "DEVIDO":
            return due, Decimal("0")
        if destination == "PENDENTE_SUSPENSO":
            return Decimal("0"), pending
        return Decimal("0"), Decimal("0")

    @api.model
    def compute_simples_nacional(
        self,
        cclass,
        base,
        crt,
        date=None,
        is_value=0.0,
        p_ibs=0.0,
        p_cbs=0.0,
        gov_entity_type=None,
        activity_code=None,
    ):
        """Compute IBS/CBS of a Simples Nacional operation (NT 2026.005).

        Differs from the regular regime on every axis: the rate is not derived
        from the cClassTrib but received from the Simples effective rate
        (``p_ibs``/``p_cbs``), the cClassTrib only resolves the type of gross
        revenue (``tpRBSN``), and two matrices decide the destination of the
        amounts (due, or pending/suspended).

        :param cclass: cClassTrib, used to resolve ``tpRBSN``
        :param base: operation value, without the Imposto Seletivo
        :param crt: company regime (1, 2 or 3)
        :param is_value: Imposto Seletivo, already computed and passed through
        :param p_ibs: Simples effective rate for IBS, in percent
        :param p_cbs: Simples effective rate for CBS, in percent
        :param gov_entity_type: ``tpEnteGov`` of the gCompraGov group
        :param activity_code: ``cAtivSN``; without it the official rule does
            not calculate (and this is not an error)
        """
        date = fields.Date.to_date(date) or fields.Date.context_today(self)
        result = {
            "status": "calculated",
            "errors": [],
            "revenue_type": False,
            "revenue": 0.0,
            "base": 0.0,
            "p_ibs": 0.0,
            "p_cbs": 0.0,
            "generates_ibs": True,
            "ibs": {"due": 0.0, "pending": 0.0},
            "cbs": {"due": 0.0, "pending": 0.0},
            "is": float(self._to_decimal(is_value)),
            "total": 0.0,
            "annex": "",
        }

        classification = self._classification(cclass, date)
        if not classification:
            return self._fail(
                result, "RTC-101", f"unknown cClassTrib {cclass} at {date}"
            )
        revenue_type = self.env["l10n_br_fiscal.rtc.sn.revenue.type"].find(
            classification.rtc_sn_revenue_type, date
        )
        if not revenue_type:
            return self._fail(
                result,
                "RTC-102",
                f"cClassTrib {cclass} has no Simples revenue type",
            )
        regime = self.env["l10n_br_fiscal.rtc.sn.regime"].find(crt, date)
        if not regime:
            return self._fail(
                result, "RTC-103", f"no Simples apuration regime for CRT {crt}"
            )

        # gross revenue of the item: zero when the revenue type does not
        # compose revenue, plus the IS when the type says so (currently never
        # in the official load, kept as a per-period parameter)
        is_decimal = self._to_decimal(is_value)
        base_decimal = self._to_decimal(base)
        if revenue_type.composes_revenue:
            revenue = base_decimal + (
                is_decimal if revenue_type.is_composes_revenue else Decimal("0")
            )
        else:
            revenue = Decimal("0")

        result["revenue_type"] = revenue_type.code
        result["revenue"] = self._money(revenue)

        activity = self.env["l10n_br_fiscal.rtc.sn.activity"].find(activity_code, date)
        if not activity:
            # NT 2026.005 s. 5.3.4: cAtivSN absent or invalid means "not
            # calculated", and it is not an error.
            result["status"] = "not_calculated"
            return result
        result["annex"] = activity.annex or ""

        # public purchase: the CBS gives part of its rate to the IBS
        p_ibs_decimal = self._to_decimal(p_ibs)
        p_cbs_decimal = self._to_decimal(p_cbs)
        if gov_entity_type:
            entity = int(gov_entity_type)
            if entity == 1:
                p_cbs_decimal = self._r8(p_cbs_decimal + p_ibs_decimal)
                p_ibs_decimal = Decimal("0")
            elif entity in (2, 3, 4):
                transition = self.env["l10n_br_fiscal.rtc.sn.transition"].find(date)
                if not transition:
                    return self._fail(
                        result,
                        "RTC-104",
                        f"no Simples transition factor at {date}",
                    )
                factor = self._to_decimal(transition.factor)
                p_ibs_decimal = self._r8(p_ibs_decimal + factor * p_cbs_decimal)
                p_cbs_decimal = self._r8((Decimal("1") - factor) * p_cbs_decimal)

        result["p_ibs"] = float(p_ibs_decimal)
        result["p_cbs"] = float(p_cbs_decimal)
        result["generates_ibs"] = regime.generates_ibs

        factor = self._to_decimal(revenue_type.revenue_factor)
        result["base"] = self._money(revenue * factor)

        def tax_value(rate):
            if factor == 0:
                return Decimal("0")
            return self._r8(revenue * factor * self._r8(rate / HUNDRED))

        ibs_due, ibs_pending = self._sn_destination(
            regime.destination_pending
            if revenue_type.pending
            else regime.destination_due,
            tax_value(p_ibs_decimal),
            tax_value(p_ibs_decimal),
        )
        cbs_due, cbs_pending = self._sn_destination(
            regime.destination_pending
            if revenue_type.pending
            else regime.destination_due,
            tax_value(p_cbs_decimal),
            tax_value(p_cbs_decimal),
        )
        if not regime.generates_ibs:
            # CRT=2: the IBS is declared by the issuer outside this event
            ibs_due = Decimal("0")
            ibs_pending = Decimal("0")

        result["ibs"] = {
            "due": self._money(ibs_due),
            "pending": self._money(ibs_pending),
        }
        result["cbs"] = {
            "due": self._money(cbs_due),
            "pending": self._money(cbs_pending),
        }
        result["total"] = self._money(
            ibs_due + cbs_due + self._to_decimal(result["is"])
        )
        return result
