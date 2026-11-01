# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
from datetime import timedelta

from psycopg2 import IntegrityError

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..constants import TOKEN_EMISSION_LIMIT, TOKEN_EMISSION_WINDOW_MINUTES

_logger = logging.getLogger(__name__)


class DereToken(models.Model):
    _name = "l10n_br_dere.token"
    _description = "Receita Integra access token"

    client_id = fields.Char(required=True, index=True)
    access_token = fields.Char(groups="l10n_br_dere.group_manager")
    expires_at = fields.Datetime(groups="l10n_br_dere.group_manager")
    issued_at = fields.Datetime(groups="l10n_br_dere.group_manager")
    emission_log = fields.Text(
        groups="l10n_br_dere.group_manager",
        help="JSON list of token emission times for this client id.",
    )

    _sql_constraints = [
        (
            "client_id_uniq",
            "unique(client_id)",
            "There is already a Receita Integra token for this client id.",
        )
    ]

    @api.model
    def _lock(self, client_id):
        """Return the token row for ``client_id``, locked for this transaction."""
        if not client_id:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        cr = self.env.cr
        cr.execute(
            "SELECT id FROM l10n_br_dere_token WHERE client_id = %s FOR UPDATE",
            (client_id,),
        )
        row = cr.fetchone()
        if not row:
            try:
                with cr.savepoint():
                    self.sudo().create({"client_id": client_id})
            except IntegrityError:
                _logger.debug(
                    "DeRE token row for client %s was created concurrently",
                    client_id,
                    exc_info=True,
                )
            cr.execute(
                "SELECT id FROM l10n_br_dere_token WHERE client_id = %s FOR UPDATE",
                (client_id,),
            )
            row = cr.fetchone()
        if not row:
            raise UserError(
                _("Configure the Receita Integra client id and secret on the company.")
            )
        record = self.sudo().browse(row[0])
        record.invalidate_recordset()
        return record

    def _emission_times(self):
        self.ensure_one()
        if not self.emission_log:
            return []
        try:
            raw = json.loads(self.emission_log)
        except json.JSONDecodeError:
            return []
        times = []
        for item in raw:
            value = fields.Datetime.to_datetime(item)
            if value:
                times.append(value)
        return times

    def _assert_can_emit(self, now):
        """Refuse a third successful emission inside the rolling hour."""
        self.ensure_one()
        window_start = now - timedelta(minutes=TOKEN_EMISSION_WINDOW_MINUTES)
        recent = [item for item in self._emission_times() if item > window_start]
        if len(recent) >= TOKEN_EMISSION_LIMIT:
            raise UserError(
                _(
                    "Receita Integra allows %(limit)s access tokens per hour "
                    "for this client id. Wait before requesting another one."
                )
                % {"limit": TOKEN_EMISSION_LIMIT}
            )
        return recent

    def _remember_emission(self, now, recent):
        self.ensure_one()
        recent.append(now)
        self.emission_log = json.dumps(
            [fields.Datetime.to_string(item) for item in recent]
        )
