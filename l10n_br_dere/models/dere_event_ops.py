# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError

from ..constants import (
    DEFAULT_VER_APLIC,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1198,
    EVENT_D1199,
    TRANSIENT_HTTP_CODES,
)

ALLOWED_MOT_EXCL = frozenset({"2", "3", "9"})
PERIODIC_RECEIPT_EVENTS = (EVENT_D1101, EVENT_D1106, EVENT_D1121)


class DereEventParentMixin(models.AbstractModel):
    _name = "l10n_br_dere.event.parent.mixin"
    _description = "DeRE event operation helpers"

    def _dere_force_unlink_allowed(self):
        self.ensure_one()
        return self.env.context.get("dere_force_unlink") or (
            bool(self.company_id) and self.company_id._dere_can_force_delete()
        )

    def _event_records(self, event_type):
        self.ensure_one()
        return self.event_ids.filtered(lambda ev: ev.event_type == event_type)

    def _active_event(self, event_type):
        self.ensure_one()
        accepted = self._event_records(event_type).filtered(
            lambda ev: ev.state == "accepted"
        )
        if not accepted:
            return self.env["l10n_br_dere.event"]
        latest = accepted.sorted("id")[-1]
        if latest.tp_oper == "3":
            return self.env["l10n_br_dere.event"]
        return latest

    def _latest_event(self, event_type):
        self.ensure_one()
        return self._event_records(event_type).sorted("id")[-1:]

    def _apply_return_content(self, event, payload):
        """Persist the D-9xxx content of an accepted return."""
        return True

    def _period_is_closed(self):
        return False

    def _first_closing_accepted(self):
        return False

    def _can_create_next_event(self, event_type):
        return False

    def _assert_receipt_period(self, receipt, per_apur):
        expected = (per_apur or "").replace("-", "")
        if not receipt or len(receipt) < 11 or receipt[5:11] != expected:
            raise UserError(
                _(
                    "The previous receipt must belong to assessment period %s "
                    "(characters 6 to 11 of the receipt)."
                )
                % (per_apur or "")
            )

    def _prepare_oper_extra(self, event_type, tp_oper="1", extra=None):
        self.ensure_one()
        vals = dict(extra or {})
        vals["tpOper"] = tp_oper
        if event_type in (EVENT_D1198, EVENT_D1199) and tp_oper != "1":
            raise UserError(_("%s only admits inclusion (tpOper 1).") % event_type)
        if event_type != EVENT_D1121 and tp_oper == "4":
            raise UserError(_("Only D-1121 admits rectification (tpOper 4)."))
        if tp_oper == "3":
            mot_excl = vals.get("motExcl")
            if mot_excl not in ALLOWED_MOT_EXCL:
                raise UserError(
                    _(
                        "Exclusion requires motExcl 2, 3 or 9. Judicial "
                        "exclusions (motExcl 1) need event D-1021."
                    )
                )
        if tp_oper in ("2", "3") and event_type in PERIODIC_RECEIPT_EVENTS:
            active = self._active_event(event_type)
            if not active or not active.nr_recibo:
                raise UserError(
                    _(
                        "An accepted %(event_type)s receipt is required "
                        "before tpOper %(tp_oper)s."
                    )
                    % {"event_type": event_type, "tp_oper": tp_oper}
                )
            per_apur = vals.get("perApur") or getattr(self, "per_apur", False)
            self._assert_receipt_period(active.nr_recibo, per_apur)
            vals["nrRecibo"] = active.nr_recibo
        if tp_oper in ("1", "4") and event_type in PERIODIC_RECEIPT_EVENTS:
            vals.pop("nrRecibo", None)
        return vals

    def _can_include_event(self, event_type):
        self.ensure_one()
        if event_type in (EVENT_D1198, EVENT_D1199):
            latest = self._latest_event(event_type)
            if latest and latest.state == "sent":
                return False
            if latest and latest.state in ("draft", "generated"):
                return True
            if latest and latest.state == "accepted":
                return self._can_create_next_event(event_type)
            return event_type == EVENT_D1199 or self._can_create_next_event(event_type)
        if event_type == EVENT_D1121 and self._first_closing_accepted():
            return False
        latest = self._latest_event(event_type)
        if latest and latest.state == "sent":
            return False
        if latest and latest.state in ("draft", "generated"):
            return latest.tp_oper == "1"
        return not bool(self._active_event(event_type))

    def _can_replace_or_exclude(self, event_type):
        self.ensure_one()
        if self._period_is_closed():
            return False
        if event_type == EVENT_D1121 and self._first_closing_accepted():
            return False
        latest = self._latest_event(event_type)
        if latest and latest.state == "sent":
            return False
        if (
            latest
            and latest.state in ("draft", "generated")
            and latest.tp_oper in ("2", "3")
        ):
            return True
        return bool(self._active_event(event_type))

    def _assert_can_create_oper(self, event_type, tp_oper):
        self.ensure_one()
        if event_type in (EVENT_D1198, EVENT_D1199):
            return
        latest = self._latest_event(event_type)
        if latest and latest.state in ("draft", "generated"):
            return
        if tp_oper == "1":
            if self._active_event(event_type):
                raise UserError(
                    _(
                        "Event %s is already active. Replace (tpOper 2) or "
                        "exclude (tpOper 3) it."
                    )
                    % event_type
                )
            if event_type == EVENT_D1121 and self._first_closing_accepted():
                raise UserError(
                    _(
                        "After the first accepted D-1199, D-1121 only admits "
                        "rectification (tpOper 4)."
                    )
                )
            return
        if tp_oper in ("2", "3"):
            if self._period_is_closed():
                raise UserError(
                    _("A closed period cannot replace or exclude %s.") % event_type
                )
            if event_type == EVENT_D1121 and self._first_closing_accepted():
                raise UserError(
                    _(
                        "After the first accepted D-1199, D-1121 only admits "
                        "rectification (tpOper 4)."
                    )
                )
            if not self._active_event(event_type):
                raise UserError(_("No active %s to replace or exclude.") % event_type)
            return
        if tp_oper == "4":
            if event_type != EVENT_D1121:
                raise UserError(_("Only D-1121 admits rectification (tpOper 4)."))
            if (
                not self._first_closing_accepted()
                or getattr(self, "state", "") != "reopened"
            ):
                raise UserError(
                    _(
                        "D-1121 rectification requires an accepted D-1199 and "
                        "an accepted D-1198."
                    )
                )

    def _create_oper_event(self, event_type, tp_oper="1", parent_field=None):
        self.ensure_one()
        events = self._event_records(event_type)
        pending = events.filtered(lambda ev: ev.state in ("draft", "generated"))[:1]
        if pending:
            pending.tp_oper = tp_oper
            return pending
        sent = events.filtered(lambda ev: ev.state == "sent")
        if sent:
            raise UserError(
                _("Wait for the sent %s consult before creating another operation.")
                % event_type
            )
        self._assert_can_create_oper(event_type, tp_oper)
        company = self.company_id
        return self.env["l10n_br_dere.event"].create(
            {
                parent_field: self.id,
                "event_type": event_type,
                "tp_oper": tp_oper,
                "tp_amb": company.dere_tp_amb or "2",
                "ver_aplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            }
        )

    def _default_periodic_tp_oper(self, event_type):
        self.ensure_one()
        if event_type == EVENT_D1121 and self._first_closing_accepted():
            return "4"
        if self._active_event(event_type):
            return "2"
        return "1"

    def _unknown_transmission_action(self):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Transmission unknown"),
                "message": _(
                    "The DeRE batch request failed before a protocol was "
                    "received. Check the transmission before sending again."
                ),
                "type": "warning",
                "sticky": True,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def _apply_send_result(self, batch, events, result):
        """Persist the send outcome without losing generated events on retries.

        A 2xx response without a protocol, or a transient HTTP error, leaves
        the batch unknown so the user can inspect the gateway before resending.
        Only a definitive application error marks the events as rejected.
        """
        protocol = self._extract_protocol(result.get("text") or "")
        status = result.get("status_code") or 0
        accepted = bool(result.get("ok") and protocol)
        if accepted:
            batch.write(
                {
                    "state": "sent",
                    "response_text": result.get("text"),
                    "protocol": protocol,
                }
            )
            batch._schedule_next_consult()
            events.write({"state": "sent", "protocol": protocol})
            return batch
        if result.get("ok") or status in TRANSIENT_HTTP_CODES:
            batch.write(
                {
                    "state": "unknown",
                    "response_text": result.get("text"),
                    "protocol": protocol or False,
                }
            )
            return self._unknown_transmission_action()
        batch.write(
            {
                "state": "error",
                "response_text": result.get("text"),
                "protocol": protocol or False,
            }
        )
        events.write({"state": "rejected", "protocol": protocol or False})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Transmission rejected"),
                "message": _("Receita Integra rejected the batch: %s")
                % (result.get("text") or ""),
                "type": "danger",
                "sticky": True,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }
