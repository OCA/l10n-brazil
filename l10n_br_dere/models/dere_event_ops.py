# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import re

import requests
from lxml import etree

from odoo import Command, _, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_br_dere_spec.models import xsd_validator

from ..constants import (
    DEFAULT_VER_APLIC,
    EVENT_D1101,
    EVENT_D1106,
    EVENT_D1121,
    EVENT_D1198,
    EVENT_D1199,
    PROTOCOL_RE,
    TRANSIENT_HTTP_CODES,
)
from . import xml_builder

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

    def _event_can_be_generated(self, event_type):
        return self._can_include_event(event_type)

    def _next_events(self, event_types):
        """Return the first generated event of ``event_types``, in order."""
        self.ensure_one()
        for event_type in event_types:
            events = self.event_ids.filtered(
                lambda ev, current=event_type: ev.event_type == current
                and ev.xml_content
                and ev.state == "generated"
            )
            if events:
                return events[:1]
        return self.env["l10n_br_dere.event"]

    def _activity_codes(self, table_code):
        return self.company_id.dere_activity_ids.filtered(
            lambda act: act.table_code == table_code
        ).mapped("code")

    def _dere_header_validity_vals(self):
        """Return the validity keys of the event header."""
        self.ensure_one()
        return {
            "iniValid": fields.Date.to_string(self.ini_valid),
            "fimValid": fields.Date.to_string(self.fim_valid)
            if self.fim_valid
            else False,
        }

    def _header_vals(self, extra=None, event_type=None, tp_oper="1"):
        self.ensure_one()
        company = self.company_id
        extra = extra or {}
        extra = self._prepare_oper_extra(
            event_type, extra.get("tpOper") or tp_oper or "1", extra
        )
        tp_oper = extra.get("tpOper") or tp_oper or "1"
        vals = {
            "id": self.env["l10n_br_dere.event"]._generate_event_id(
                event_type=event_type,
                company=company,
                tp_amb=company.dere_tp_amb or "2",
            ),
            "tpOper": tp_oper,
            "tpAmb": company.dere_tp_amb or "2",
            "aplicEmi": "1",
            "verAplic": company.dere_ver_aplic or DEFAULT_VER_APLIC,
            "nrInsc": company._dere_cnpj_root(),
            **self._dere_header_validity_vals(),
        }
        vals.update(extra)
        if not vals["nrInsc"] or len(vals["nrInsc"]) != 8:
            raise UserError(_("Set a valid 8-digit CNPJ root on the company."))
        return vals

    def _apply_return_content(self, event, payload):
        """Persist the D-9xxx content of an accepted return."""
        return True

    def _dere_after_return(self, event):
        """Update the parent state once ``event`` has its RFB return."""
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

    def _get_dere_certificate(self):
        self.ensure_one()
        return self.company_id._dere_signing_certificate()

    def _dere_batch_vals(self, events):
        """Return the name and parent link of the batch that sends ``events``."""
        raise NotImplementedError()

    def _send_next_events(self, event_types):
        result = True
        for rec in self:
            action = rec._send_events(rec._next_events(event_types))
            if isinstance(action, dict):
                result = action
        return result

    def _send_events(self, events):
        self.ensure_one()
        if not events:
            raise UserError(_("There is no generated event to send."))
        self._assert_send_order(events.mapped("event_type"))
        certificado = self._get_dere_certificate()
        signed_events = []
        for ev in events:
            signed_xml = xml_builder.sign_event(
                ev.xml_content, certificado, ev.event_id_attr
            )
            ev._assert_valid_xml(signed_xml, signed=True)
            signed_events.append({"id": ev.event_id_attr, "xml": signed_xml})
        xml = xml_builder.build_lote(self.company_id._dere_cnpj_root(), signed_events)
        lote_errors = xsd_validator.validate_lote(xml)
        if lote_errors:
            raise UserError(
                _("DeRE batch XML failed official XSD validation:\n%s")
                % "\n".join(lote_errors[:8])
            )
        batch = self.env["l10n_br_dere.batch"].create(
            {
                **self._dere_batch_vals(events),
                "tp_amb": self.company_id.dere_tp_amb or "2",
                "event_ids": [Command.set(events.ids)],
                "xml_content": xml,
            }
        )
        try:
            result = self.env["l10n_br_dere.receita.integra"].send_batch(
                self.company_id, xml
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            batch.write({"state": "unknown", "response_text": str(exc)})
            return self._unknown_transmission_action()
        return self._apply_send_result(batch, events, result)

    def _dere_consultable_batches(self):
        self.ensure_one()
        return self.batch_ids

    def action_consult_results(self):
        consulted = self.env["l10n_br_dere.batch"]
        for rec in self:
            transmitted = rec._dere_consultable_batches().filtered("protocol")
            if not transmitted:
                raise UserError(_("There is no sent batch with a protocol to consult."))
            batches = transmitted.filtered(lambda batch: batch.state == "sent")
            batches.action_consult()
            consulted |= batches
        if not consulted:
            # The scheduled consult job may have processed the batch already.
            return self._notify_and_reload(
                _("Nothing to consult"),
                _("Every transmitted batch was already processed."),
            )
        return True

    def _notify_and_reload(self, title, message, notification_type="info"):
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": title,
                "message": message,
                "type": notification_type,
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def _replace_occurrences(self, events, occurrences):
        events.occurrence_ids.unlink()
        self.env["l10n_br_dere.event.occurrence"].create(
            [
                {
                    "event_id": event.id,
                    "codigo": item.get("codigo") or "0",
                    "descricao": item.get("descricao") or "",
                    "tipo": item.get("tipo") or "1",
                    "localizacao": item.get("localizacao"),
                }
                for event in events
                for item in occurrences
            ]
        )

    def apply_return(
        self,
        event,
        cd_retorno,
        desc_retorno=None,
        nr_recibo=None,
        protocol=None,
        occurrences=None,
        payload=None,
    ):
        event.write(
            {
                "cd_retorno": cd_retorno,
                "desc_retorno": desc_retorno,
                "nr_recibo": nr_recibo,
                "protocol": protocol or event.protocol,
                "state": "accepted" if cd_retorno == "1" else "rejected",
                **event._return_payload_vals(payload),
            }
        )
        event._check_return_schema()
        parent = event._return_parent()
        parent._dere_after_return(event)
        if occurrences:
            self._replace_occurrences(event, occurrences)
        parent._apply_return_content(event, payload)
        return True

    def _reject_batch_events(self, batch, parsed):
        events = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        events.with_context(dere_force_event_write=True).write(
            {
                "state": "rejected",
                "cd_retorno": "0",
                "desc_retorno": parsed.get("descResposta") or parsed.get("descRetorno"),
            }
        )
        occurrences = parsed.get("ocorrencias") or []
        if occurrences:
            self._replace_occurrences(events, occurrences)

    def _dere_same_event_type(self, event_type, tp_ev):
        """Match a return tpEv that may omit the hyphen of the stored type."""
        return (event_type or "").replace("-", "") == (tp_ev or "").replace("-", "")

    def _apply_consult_result(self, batch, xml_content):
        self.ensure_one()
        if not xml_content or "<" not in xml_content:
            return False
        try:
            parsed = xml_builder.parse_return(xml_content)
        except etree.XMLSyntaxError:
            return False
        cd_resposta = str(parsed.get("cdResposta") or "")
        if cd_resposta == "1":
            return False
        if cd_resposta in ("4", "5", "7", "9"):
            batch.state = "error"
            self._reject_batch_events(batch, parsed)
            return False
        protocol = (
            parsed.get("protocoloLote") or parsed.get("protocolo") or batch.protocol
        )
        applied = False
        for item in parsed.get("events") or []:
            target = batch.event_ids
            if item.get("id"):
                event_id = item["id"]
                matched = target.filtered(
                    lambda ev, current=event_id: ev.event_id_attr == current
                )
                if matched:
                    target = matched
            if item.get("tpEv"):
                event_type = item["tpEv"]
                target = target.filtered(
                    lambda ev, current=event_type: self._dere_same_event_type(
                        ev.event_type, current
                    )
                )
            if not target:
                continue
            self.apply_return(
                target[0],
                item.get("cdRetorno") or "0",
                desc_retorno=item.get("descRetorno"),
                nr_recibo=item.get("nrRecibo"),
                protocol=item.get("protocoloLote") or protocol,
                occurrences=item.get("ocorrencias"),
                payload=item,
            )
            applied = True
        pending = batch.event_ids.filtered(lambda ev: ev.state == "sent")
        if pending:
            return applied
        if cd_resposta in ("2", "3") or batch.event_ids:
            batch.state = "done"
            return True
        return applied

    def _extract_protocol(self, text):
        if not text:
            return False
        stripped = text.strip()
        if re.fullmatch(PROTOCOL_RE, stripped):
            return stripped
        if stripped.startswith("{"):
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return False
            return payload.get("protocoloLote") or payload.get("protocolo") or False
        if "<" not in stripped:
            return False
        try:
            parsed = xml_builder.parse_return(text)
        except etree.XMLSyntaxError:
            return False
        return parsed.get("protocoloLote") or parsed.get("protocolo") or False

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
