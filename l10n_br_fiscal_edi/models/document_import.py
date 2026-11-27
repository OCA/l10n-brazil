# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

# pylint: disable=consider-merging-classes-inherited

import logging
import re
import unicodedata
import zipfile
from contextlib import closing
from io import BytesIO

from erpbrasil.base.fiscal.cnpj_cpf import formata
from psycopg2 import OperationalError
from psycopg2.errors import LockNotAvailable

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.sql_db import db_connect
from odoo.tools.misc import file_open, format_datetime

from odoo.addons.l10n_br_fiscal.constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
    DOCUMENT_ISSUER_PARTNER,
    DOCUMENT_STATE_DRAFT,
    FISCAL_IN,
    FISCAL_OUT,
)

from ..constants.fiscal import DOCUMENT_STATE_AUTHORIZED
from ..tools import EDI_IMPORT_DEMO, EDI_IMPORT_NO_CREATE, EdiImportConcurrencyError

_logger = logging.getLogger(__name__)

# Context key that carries, to the end of the import, the last partner that existed
# before it started: the partners above it were created by the file.
LAST_PARTNER_CONTEXT_KEY = "edi_import_last_partner_id"


class Document(models.Model):
    """Import of fiscal files into draft documents, whatever the type of the file.

    The reader of each type (NF-e, CT-e, NFS-e, MDF-e) is a module that chains
    ``_edi_import_read``, ``_edi_import_create`` and, when it needs to, the other
    steps. This module orchestrates: it reads, finds the company, refuses what must
    not enter, creates the document faithful to the file and suggests the review.
    """

    _inherit = "l10n_br_fiscal.document"

    import_warning = fields.Text(
        compute="_compute_import_warning",
        help="What the imported document still lacks to be reviewed.",
    )

    import_can_create_products = fields.Boolean(
        compute="_compute_import_can_create_products",
        help="The user may create products, which the action of the imported "
        "documents the company issued needs.",
    )

    import_missing_products = fields.Boolean(
        compute="_compute_import_missing_products",
        help="Some line has the code of a product in the file, a confirmed unit and "
        "no product yet, which the action to create the missing products would "
        "resolve.",
    )

    import_partner_warning = fields.Text(
        copy=False,
        readonly=True,
        help="Where the data of a partner in the file differ from its registry, "
        "which the import never changes, and the partners that were matched by name. "
        "It is the picture of the day it was checked (import_partner_checked), and "
        "the button to check again updates it.",
    )

    import_without_protocol = fields.Boolean(
        copy=False,
        readonly=True,
        help="The file of a document the company issued elsewhere carries no "
        "authorization protocol: it cannot be confirmed as authorized.",
    )

    import_partner_checked = fields.Datetime(
        copy=False,
        readonly=True,
        help="When the data of the partners in the file were last compared with "
        "their registry: at the import, or when somebody checked again.",
    )

    @api.depends(
        "imported_document",
        "import_without_protocol",
        "fiscal_operation_id",
        "import_partner_warning",
        "fiscal_amount_total",
        "fiscal_line_ids.fiscal_operation_id",
        "fiscal_line_ids.fiscal_operation_line_id",
        "fiscal_line_ids.partner_ncm_code",
        "fiscal_line_ids.ncm_id",
        "fiscal_line_ids.uom_id",
        "fiscal_line_ids.import_uom_id",
        "fiscal_line_ids.partner_uom_code",
    )
    def _compute_import_warning(self):
        for document in self:
            document.import_warning = (
                "\n".join(document._edi_import_warnings()) or False
            )

    def _edi_no_payable_reason(self):
        """Why the imported document has no amount to pay, as a text for the
        person, or False. The type of the document decides it: a document that is
        only registered, such as a freight that the company does not owe, answers
        here. The document shows the text as a warning, and the modules that
        generate the invoice refuse it."""
        self.ensure_one()
        return False

    def _edi_import_warnings(self):
        """Messages that tell what an imported document still lacks."""
        self.ensure_one()
        messages = []
        if not self.imported_document:
            return messages
        if self.fiscal_line_ids and not self.fiscal_operation_id:
            messages.append(
                _(
                    "No fiscal operation matches the CFOP of the document: choose the "
                    "fiscal operation of the document and the operation line of "
                    "each line."
                )
            )
        reason = self._edi_no_payable_reason()
        if reason:
            messages.append(reason)
        if self.import_without_protocol:
            messages.append(
                _(
                    "The file of this document, issued by the company, has no "
                    "authorization protocol: it cannot be confirmed as authorized. "
                    "Import the file with the protocol."
                )
            )
        for line in self.fiscal_line_ids:
            if line.fiscal_operation_id and not line.fiscal_operation_line_id:
                messages.append(
                    _(
                        "%(line)s: more than one operation line fits the operation: "
                        "choose the operation line of the line."
                    )
                    % {"line": line.name}
                )
            if line.partner_ncm_code and not line.ncm_id:
                messages.append(
                    _("%(line)s: the NCM %(ncm)s is not in the registry.")
                    % {"line": line.name, "ncm": line.partner_ncm_code}
                )
            if line._import_unit_unconfirmed():
                messages.append(
                    _("%(line)s: the unit %(uom)s has no match in the units.")
                    % {"line": line.name, "uom": line.partner_uom_code}
                )
        if self.import_partner_warning:
            messages.append(
                _("Partner data, as compared with the registry on %(date)s:")
                % {
                    "date": format_datetime(
                        self.env, self.import_partner_checked or self.create_date
                    )
                }
            )
            messages.extend(self.import_partner_warning.splitlines())
        return messages

    @api.model
    def _edi_import_files(self, files, dfe_document=None):
        """Import fiscal files as draft documents, each one in its own savepoint.

        :param files: list of ``(name, bytes)``; a zip stands for the files in it
        :param dfe_document: ``l10n_br_fiscal_dfe.document`` the files came from
        :return: ``(documents, errors, warnings)``; ``errors`` and ``warnings`` are
            lists of ``(name, message)``. A note that was already imported is a
            warning, and its document is returned.
        """
        # The context of a window action may carry ``default_*`` keys meant for the
        # records of that window: they would fill the fields of the documents and of
        # the lines the import creates.
        # (``with_context(**kwargs)`` would add to the context, not replace it.)
        service = self.with_env(
            self.env(
                context={
                    key: value
                    for key, value in self.env.context.items()
                    if not key.startswith("default_")
                }
            )
        )
        documents = self.browse()
        errors, warnings = [], []
        for name, content in service._edi_import_expand(files):
            try:
                with self.env.cr.savepoint():
                    document, created = service._edi_import_file(
                        name, content, dfe_document=dfe_document
                    )
                documents |= document
                if not created:
                    warnings.append(
                        (
                            name,
                            _(
                                "This note was already imported; the existing "
                                "document was opened."
                            ),
                        )
                    )
            except UserError as error:
                _logger.info("Import of %s refused: %s", name, error)
                errors.append((name, str(error)))
            except Exception as error:  # pylint: disable=broad-except
                if (
                    isinstance(error, OperationalError)
                    and error.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY
                ):
                    # not an error of the file: the whole call must run again
                    raise
                _logger.warning("Import of %s failed", name, exc_info=True)
                errors.append(
                    (
                        name,
                        _(
                            "The file could not be imported because of an "
                            "unexpected error. Send it to the support."
                        ),
                    )
                )
        return documents, errors, warnings

    @api.model
    def _edi_import_demo_files(self, module, relative_paths):
        """Import the sample files that a module ships in its demo data.

        Called from the ``demo`` XML of the modules that read a type of file, so that
        the documents of the demo are imported, reviewed and confirmed by the same
        service as the ones of a person. A file that fails stops the installation:
        a broken demo must show up at once.

        :param module: name of the module that holds the files
        :param relative_paths: paths of the files inside the module
        :return: the imported documents
        """
        files = []
        for path in relative_paths:
            with file_open(f"{module}/{path}", "rb") as sample:
                files.append((path.rsplit("/", 1)[-1], sample.read()))
        documents, errors, _warnings = self.with_context(
            **{EDI_IMPORT_DEMO: True}
        )._edi_import_files(files)
        if errors:
            raise UserError("\n".join(f"{name}: {message}" for name, message in errors))
        return documents

    @api.model
    def _edi_import_expand(self, files):
        """Yield ``(name, content)`` of each file, a zip standing for what it holds
        (one level, no folders, no ``__MACOSX/``): ``zip/file``."""
        for name, content in files:
            if not zipfile.is_zipfile(BytesIO(content)):
                yield name, content
                continue
            with zipfile.ZipFile(BytesIO(content)) as archive:
                for member in archive.infolist():
                    if member.is_dir() or member.filename.startswith("__MACOSX/"):
                        continue
                    yield f"{name}/{member.filename}", archive.read(member)

    @api.model
    def _edi_import_file(self, name, content, dfe_document=None):
        """Import one file. Return ``(document, created)``: ``created`` is False
        when the note was already imported and the existing document is returned.
        """
        parsed = self._edi_import_read(name, content)
        if parsed is None:
            raise UserError(
                _("The file %s is not a fiscal document that can be imported.") % name
            )
        company, role = self._edi_import_company(parsed)
        self._edi_import_lock(company, parsed.access_key)
        existing = self.with_company(company)._edi_import_find_existing(parsed, company)
        if existing:
            return existing, False
        if self._edi_import_committed_elsewhere(parsed, company):
            raise EdiImportConcurrencyError(
                f"The note {name} was imported by a concurrent transaction."
            )
        self._edi_import_check(parsed, company)
        last_partner = self.env["res.partner"].search([], order="id desc", limit=1)
        try:
            document = (
                self.with_company(company)
                .with_context(**{EDI_IMPORT_NO_CREATE: True})
                ._edi_import_create(parsed, company, role)
            )
        except AccessError as error:
            raise UserError(self._edi_import_access_denied(parsed, error)) from error
        if (
            parsed.document_type_code
            and document.document_type_id.code != parsed.document_type_code
        ):
            raise UserError(
                _(
                    "The reader of %(file)s created a document of type %(created)s "
                    "for a file of type %(declared)s."
                )
                % {
                    "file": name,
                    "created": document.document_type_id.code or "-",
                    "declared": parsed.document_type_code,
                }
            )
        document.with_context(
            **{LAST_PARTNER_CONTEXT_KEY: last_partner.id}
        )._edi_import_after_create(parsed, role)
        document.with_context(
            **{LAST_PARTNER_CONTEXT_KEY: last_partner.id}
        )._edi_import_check_partners(parsed)
        document._edi_import_suggest()
        # A note the company issued has to bring the protocol of its authorization:
        # without it the document stays in typing (the readers of a type that has no
        # protocol, the national NFS-e, declare the file authorized).
        document.import_without_protocol = (
            document.issuer == DOCUMENT_ISSUER_COMPANY and parsed.status != "authorized"
        )
        return document, True

    @api.model
    def _edi_import_read(self, name, content):
        """Read the bytes of a file. Each reader returns an ``EdiParsedFile`` or
        calls ``super()``; the base answers that the file is not recognized."""
        return None

    @api.model
    def _edi_import_company(self, parsed):
        """Company that the file is addressed to, in the order of ``company_vats``.

        The company is looked for with sudo, because the user does not read the
        companies that are not theirs; access and company switcher are then
        checked without it, before anything is created.
        """
        company = self.env["res.company"]
        role = file_vat = False
        for candidate_role, vat in parsed.company_vats:
            company = (
                self.env["res.company"]
                .sudo()
                .search([("partner_id.cnpj_cpf_stripped", "=", vat)], limit=1)
            )
            if company:
                role, file_vat = candidate_role, vat
                break
        if not company:
            raise UserError(
                _("No company of this database is the recipient or the issuer of %s.")
                % parsed.file_name
            )
        company = company.sudo(False)
        if not self.env.su and company not in self.env.user.company_ids:
            # The name of a company the user does not have is not read nor told: the
            # CNPJ of the file says which one it is
            raise UserError(
                _(
                    "You have no access to the company with the CNPJ %s, which the "
                    "file is for."
                )
                % formata(file_vat)
            )
        if company not in self.env.companies:
            raise UserError(
                _(
                    "The note is for the company %s, which is not selected in the "
                    "company switcher. Select it and import again."
                )
                % company.sudo().display_name
            )
        return company, role

    @api.model
    def _edi_import_partner_hint(self, parsed):
        """Name and CNPJ/CPF of the partner the file needs to be registered, as
        ``(name, vat)``. A reader that knows the name overrides it; the base knows
        only the document of the issuer."""
        return "", parsed.issuer_vat

    @api.model
    def _edi_import_access_denied(self, parsed, error):
        """Message for the file of a user who may not do something that the import
        needs: the registration of a partner has its own, any other says what the
        system refused (it names the model and the operation) and what to do."""
        if "res.partner" in str(error) and not self.env[
            "res.partner"
        ].check_access_rights("create", raise_exception=False):
            return self._edi_import_partner_denied(parsed)
        return _(
            "The file %(file)s could not be imported because you do not have a "
            "permission that the import needs: %(error)s Ask for the permission to "
            "whoever manages the access, and import the file again."
        ) % {"file": parsed.file_name, "error": error.args[0] if error.args else ""}

    @api.model
    def _edi_import_partner_denied(self, parsed):
        """Message for a user who cannot create contacts when the file needs one."""
        name, vat = self._edi_import_partner_hint(parsed)
        partner = " ".join(
            part
            for part in (name, formata(vat) and f"(CNPJ/CPF {formata(vat)})")
            if part
        )
        return _(
            "The file %(file)s requires registering the partner %(partner)s, and you "
            "are not allowed to create contacts. Ask someone who can to register "
            "it, or ask for the permission, and import the file again."
        ) % {"file": parsed.file_name, "partner": partner or _("(unknown)")}

    @api.model
    def _edi_import_lock(self, company, access_key):
        """Take, until the end of the transaction, the lock of the note of this company.

        Two imports of the same note that run together would both find that it does
        not exist and both create it, and nothing in the database forbids it (an
        existing database may have duplicates, so there is no unique index). The second
        waits here until the first commits; the check that follows sees what the first
        wrote."""
        self.env.cr.execute(
            "SELECT pg_advisory_xact_lock(%s, hashtext(%s))",
            (company.id, access_key),
        )

    @api.model
    def _edi_import_check(self, parsed, company):
        """Refuse what must not enter. Extended by who knows more about the file."""
        if parsed.status == "cancelled":
            raise UserError(_("This note was cancelled by the issuer."))
        if parsed.status == "denied":
            raise UserError(_("This note was denied by the tax authority."))

    @api.model
    def _edi_import_committed_elsewhere(self, parsed, company):
        """Whether a transaction that committed after this one began already holds the
        note. The snapshot of this transaction, taken at its first query, cannot see a
        document that another transaction committed since, even after the lock of the
        note is taken; a connection of its own, with a new snapshot, can.

        An installation or an update that holds locks on the table (the demo data is
        imported while it does) would make that connection wait for ever: it waits for
        two seconds at most, and goes on without the check, as nobody else is importing
        while a module is installed."""
        if self.env.context.get(EDI_IMPORT_DEMO):
            # the demo data is imported while the module is installed, with locks on
            # the table, and nobody else imports then
            return False
        snapshot = self._edi_import_snapshot()
        with closing(db_connect(self.env.cr.dbname).cursor()) as cursor:
            try:
                cursor.execute("SET LOCAL lock_timeout = '2s'")
                cursor.execute(
                    "SELECT xmin::text::bigint FROM l10n_br_fiscal_document "
                    "WHERE document_key = %s AND company_id = %s LIMIT 1",
                    (parsed.access_key, company.id),
                )
                row = cursor.fetchone()
            except LockNotAvailable:
                row = None
            finally:
                cursor.rollback()
        return bool(row) and self._edi_import_born_after(snapshot, row[0])

    def _edi_import_snapshot(self):
        """The snapshot of this transaction: the first transaction that it does not
        see and the ones that were running and that it does not see either."""
        self.env.cr.execute("SELECT txid_current_snapshot()::text")
        return self._edi_import_parse_snapshot(self.env.cr.fetchone()[0])

    @api.model
    def _edi_import_parse_snapshot(self, text):
        """``xmin:xmax:xip,...`` of ``txid_current_snapshot`` as the 32 bits of the
        ``xmin`` of the rows: ``(xmax, {running})``."""
        modulus = 2**32
        _xmin, xmax, running = text.split(":")
        return (
            int(xmax) % modulus,
            {int(xid) % modulus for xid in running.split(",") if xid},
        )

    @api.model
    def _edi_import_born_after(self, snapshot, row_xid):
        """Whether the transaction that wrote the row is not visible to the
        snapshot. A row that the snapshot could see and does not find was deleted by
        this very transaction: that is not a concurrent import."""
        xmax, running = snapshot
        modulus = 2**32
        return (row_xid - xmax) % modulus < modulus // 2 or row_xid in running

    @api.model
    def _edi_import_find_existing(self, parsed, company):
        return self.search(
            [("document_key", "=", parsed.access_key), ("company_id", "=", company.id)],
            limit=1,
        )

    @api.model
    def _edi_import_create(self, parsed, company, role):
        """Create the draft document from the file. Each reader answers for its
        ``parsed.reader`` and calls ``super()`` for the others."""
        raise UserError(
            _("There is no importer for the files of type %s.") % parsed.reader
        )

    def _edi_import_after_create(self, parsed, role):
        """What every imported document has, whatever the reader."""
        self.ensure_one()
        issued_by_company = role == "issuer"
        self.write(
            {
                "imported_document": True,
                "issuer": (
                    DOCUMENT_ISSUER_COMPANY
                    if issued_by_company
                    else DOCUMENT_ISSUER_PARTNER
                ),
                "fiscal_operation_type": FISCAL_OUT if issued_by_company else FISCAL_IN,
                "original_xml_file_id": self.env["ir.attachment"]
                .create(
                    {
                        "name": parsed.file_name,
                        "raw": parsed.content,
                        "res_model": self._name,
                        "res_id": self.id,
                    }
                )
                .id,
            }
        )
        floor = self.env.context.get(LAST_PARTNER_CONTEXT_KEY, 0)
        new_partners = (
            self.env["res.partner"]
            .with_context(active_test=False)
            .search([("id", ">", floor), ("create_uid", "=", self.env.uid)])
        )
        if new_partners:
            # A note in the history, sent to nobody: message_post needs the email of
            # the sender, which a fiscal user may not have
            self._message_log(
                body=_("Partners created by the import: %s.")
                % ", ".join(new_partners.mapped("display_name"))
            )

    def _edi_import_partner_data(self, parsed):
        """What the file declares about its partners, as a list of
        ``(partner, EdiPartnerData)``: the partner of the registry that the document
        was linked to, and the data of the file. A reader that has them overrides it
        and calls ``super()``; the base declares nothing."""
        self.ensure_one()
        return []

    @api.model
    def _edi_import_normalize(self, value):
        """Lower case, only letters and digits (the accents are split off by NFKD and
        dropped with the punctuation): the comparison of the
        file with the registry does not report formatting."""
        value = unicodedata.normalize("NFKD", str(value or ""))
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _edi_import_registry_values(self, partner):
        """Values of the registry to compare with ``EdiPartnerData``, by attribute."""
        return {
            "name": partner.legal_name or partner.name,
            "state_tax_number": partner.l10n_br_ie_code,
            "street": partner.street_name,
            "street_number": partner.street_number,
            "district": partner.district,
            "zip_code": partner.zip,
            "city": partner.city_id.name or partner.city,
            "state_code": partner.state_id.code,
        }

    def _edi_import_check_partners(self, parsed):
        """Compare the data of the partners in the file with their registry, once,
        and keep the differences on the document. The registry is never changed."""
        self.ensure_one()
        labels = {
            "name": _("Name"),
            "state_tax_number": _("State tax number"),
            "street": _("Street"),
            "street_number": _("Number"),
            "district": _("District"),
            "zip_code": _("ZIP code"),
            "city": _("City"),
            "state_code": _("State"),
        }
        floor = self.env.context.get(LAST_PARTNER_CONTEXT_KEY)
        lines = []
        for partner, data in self._edi_import_partner_data(parsed):
            if (
                not partner
                or partner == self.company_id.partner_id
                or (floor is not None and partner.id > floor)
            ):
                continue  # none, the company itself, or created by the import
            if not data.vat:
                lines.append(
                    _(
                        "%(partner)s: the file carries no CNPJ or CPF, so the "
                        "partner was matched by name. Check that it is the right one."
                    )
                    % {"partner": partner.display_name}
                )
            registry = self._edi_import_registry_values(partner)
            for key, label in labels.items():
                declared = getattr(data, key)
                if not declared or self._edi_import_normalize(
                    declared
                ) == self._edi_import_normalize(registry[key]):
                    continue
                lines.append(
                    _(
                        '%(partner)s - %(field)s: the file says "%(file)s", the '
                        'registry says "%(registry)s".'
                    )
                    % {
                        "partner": partner.display_name,
                        "field": label,
                        "file": declared,
                        "registry": registry[key] or "",
                    }
                )
        self.import_partner_checked = fields.Datetime.now()
        self.import_partner_warning = "\n".join(lines) or False
        if lines:
            self._message_log(
                body=_("Partner data that differ from the registry: %s")
                % "; ".join(lines)
            )

    def action_import_check_partners_again(self):
        """Compare the data of the partners in the file with the registry again, now:
        the warning is the picture of when it was last checked, and a registry that was
        corrected since clears it."""
        self.ensure_one()
        attachment = self.original_xml_file_id.with_context(bin_size=False)
        parsed = attachment and self._edi_import_read(attachment.name, attachment.raw)
        if not parsed:
            raise UserError(_("The file of this document is not available to check."))
        self._edi_import_check_partners(parsed)
        return True

    def _edi_import_suggest(self):
        """Suggest the review of the document. Safe to run again: what a person
        decided is never undone."""
        for document in self.filtered("imported_document"):
            document._init_import_states()
            document._edi_import_suggest_operation()
            if document.fiscal_operation_type == FISCAL_IN:
                document._edi_import_apply_supplier_depara()
            elif document.fiscal_operation_type == FISCAL_OUT:
                document._edi_import_apply_own_products()
            for line in document.fiscal_line_ids.filtered(
                lambda line: (
                    line.import_state == "matched" and line._import_unit_unconfirmed()
                )
            ):
                line.import_state = "pending"

    def _edi_import_suggest_operation(self):
        """The operation of the document and of each line that has none, from the
        CFOP declared in the file: the inverse of the issuer for a document received,
        the very CFOP for a document the company issued elsewhere. Nothing is
        assigned when nothing matches: an empty operation would recompute the
        direction of the document."""
        self.ensure_one()
        direction = self.fiscal_operation_type
        if not direction:
            return
        operation_lines = self.env["l10n_br_fiscal.operation.line"]
        found = {
            line: operation_lines._find_by_issuer_cfop(
                line.partner_cfop_id,
                self.partner_operation_name,
                direction,
                operation=self.fiscal_operation_id,
            )
            for line in self.fiscal_line_ids.filtered(
                lambda line: not line.fiscal_operation_line_id
            )
        }
        if not self.fiscal_operation_id:
            if direction == FISCAL_IN:
                operation = self._suggest_fiscal_operation()
            else:
                votes = [op_line.fiscal_operation_id for op_line in found.values()]
                votes = [operation for operation in votes if operation]
                operation = votes and max(set(votes), key=votes.count)
            if operation:
                self.fiscal_operation_id = operation
        self._edi_import_spread_operation(found)

    def _edi_import_spread_operation(self, found=None):
        """Give the lines that have no operation the one of the document, and the
        operation line the CFOP of the file points to when it does. Used when the
        suggestion finds the operation and when a person chooses it on the header:
        the two end the same. The values and the taxes declared in the file are not
        touched, and a line that already has an operation keeps it."""
        self.ensure_one()
        if not self.fiscal_operation_id:
            return
        if found is None:
            found = self._edi_import_operation_lines_found()
        for line, operation_line in found.items():
            line.fiscal_operation_id = (
                operation_line.fiscal_operation_id or self.fiscal_operation_id
            )
            if not operation_line:
                # No line answers the CFOP of the file (a CT-e, for instance): the
                # operation line is applied only when the operation has a single
                # candidate. With more, the line is left to the person, who is warned.
                candidates = self._edi_import_operation_line_candidates(
                    line.fiscal_operation_id
                )
                operation_line = line.fiscal_operation_line_id or (
                    candidates if len(candidates) == 1 else candidates.browse()
                )
            if operation_line:
                line.fiscal_operation_line_id = operation_line

    @api.model
    def _edi_import_operation_line_candidates(self, operation):
        """The approved lines of the operation, of its type."""
        return operation.line_ids.filtered(
            lambda op_line: (
                op_line.state == "approved"
                and op_line.fiscal_operation_type == operation.fiscal_operation_type
            )
        )

    def _edi_import_operation_lines_found(self):
        """The operation line of each line that has none, by the CFOP of the file."""
        self.ensure_one()
        operation_lines = self.env["l10n_br_fiscal.operation.line"]
        return {
            line: operation_lines._find_by_issuer_cfop(
                line.partner_cfop_id,
                self.partner_operation_name,
                self.fiscal_operation_type,
                operation=self.fiscal_operation_id,
            )
            for line in self.fiscal_line_ids.filtered(
                lambda line: (
                    not line.fiscal_operation_line_id and not line.fiscal_operation_id
                )
            )
        }

    def write(self, vals):
        result = super().write(vals)
        if "fiscal_operation_id" in vals:
            for document in self.filtered("imported_document"):
                document._edi_import_spread_operation()
        return result

    def _compute_import_can_create_products(self):
        can_create = self.env["product.product"].check_access_rights(
            "create", raise_exception=False
        )
        for document in self:
            document.import_can_create_products = can_create

    @api.depends(
        "fiscal_line_ids.product_id",
        "fiscal_line_ids.uom_id",
        "fiscal_line_ids.import_uom_id",
        "fiscal_line_ids.partner_uom_code",
    )
    def _compute_import_missing_products(self):
        for document in self:
            document.import_missing_products = any(
                not line.product_id
                and line._get_partner_product_code()
                and not line._import_unit_unconfirmed()
                for line in document.fiscal_line_ids
            )

    def _edi_import_own_product(self, code):
        """The product of the company with this internal code: in a document the
        company issued, the code of the product in the file is its own."""
        self.ensure_one()
        return self.env["product.product"].search(
            [
                ("default_code", "=", code),
                ("company_id", "in", [False, self.company_id.id]),
            ],
            limit=1,
        )

    def _edi_import_apply_own_products(self):
        """Resolve the lines of a document the company issued whose code is the
        internal code of one of its products, when the unit declared is confirmed;
        otherwise the product is only suggested."""
        self.ensure_one()
        for line in self.fiscal_line_ids.filtered(
            lambda line: line.import_state in (False, "pending", "matched")
        ):
            code = line._get_partner_product_code()
            product = code and self._edi_import_own_product(code)
            if not product:
                continue
            line.product_id = product
            if line._import_unit_unconfirmed():
                line.import_state = "pending"
            else:
                line._apply_import_depara(product=product, uom=line.uom_id)

    def action_import_create_products(self):
        """Create the products that a document the company issued lacks: one for each
        distinct code declared, and resolve the lines. It is an explicit action of
        who may create products; the import itself never creates one, and a product
        that already has the code is used, not duplicated. A line whose unit was not
        confirmed is left for the review."""
        product_model = self.env["product.product"]
        if not product_model.check_access_rights("create", raise_exception=False):
            raise UserError(_("You are not allowed to create products."))
        blocked = self.env["l10n_br_fiscal.document.line"]
        for document in self:
            if not (
                document.imported_document
                and document.fiscal_operation_type == FISCAL_OUT
            ):
                raise UserError(
                    _("Products are created only for a document the company issued.")
                )
            lines = document.fiscal_line_ids.filtered(
                lambda line: not line.product_id and line._get_partner_product_code()
            )
            blocked |= lines.filtered(lambda line: line._import_unit_unconfirmed())
            by_code = {}
            for line in lines - blocked:
                code = line._get_partner_product_code()
                by_code[code] = by_code.get(code, blocked.browse()) | line
            created = product_model
            for code, group in by_code.items():
                product = document._edi_import_own_product(code)
                if not product:
                    product = product_model.with_company(document.company_id).create(
                        group[0]._edi_import_product_vals()
                    )
                    created |= product
                for line in group:
                    line.product_id = product
                    line._apply_import_depara(product=product, uom=line.uom_id)
            if created:
                document._message_log(
                    body=_("Products created by %(user)s: %(products)s")
                    % {
                        "user": self.env.user.display_name,
                        "products": ", ".join(created.mapped("display_name")),
                    }
                )
        if not blocked:
            return True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Some lines were left for the review"),
                "message": _(
                    "%(count)s line(s) have a unit that was not confirmed, and no "
                    "product was created for them. Choose the unit of each one."
                )
                % {"count": len(blocked)},
                "type": "warning",
                "sticky": True,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def _edi_import_apply_supplier_depara(self):
        """Resolve the lines whose product the buyer already mapped for this
        supplier (a previous decision of a person). A product found only by code,
        barcode or name stays a suggestion."""
        self.ensure_one()
        uom_model = self.env["uom.uom"]
        supplierinfo_model = self.env["product.supplierinfo"].sudo()
        for line in self.fiscal_line_ids.filtered(
            lambda line: line.import_state in (False, "pending", "matched")
        ):
            code = line._get_partner_product_code()
            info = code and supplierinfo_model.search(
                [("partner_id", "=", self.partner_id.id), ("product_code", "=", code)],
                limit=1,
            )
            product = info and (
                info.product_id or info.product_tmpl_id.product_variant_ids[:1]
            )
            if not product:
                continue
            line.product_id = product
            declared = uom_model._match_by_fiscal_code(line.partner_uom_code)
            learned_uom, learned_factor = line._get_supplierinfo_unit(info)
            if declared and learned_uom == declared:
                line._apply_import_depara(
                    product=product, uom=product.uom_po_id, factor=learned_factor
                )
            elif declared and declared == product.uom_po_id:
                line._apply_import_depara(product=product, uom=declared, factor=1.0)
            elif line.uom_id:
                line.import_state = "matched"

    def action_import_confirm_suggestions(self):
        """Resolve at once the lines whose product is a suggestion: the confirmation
        of whoever reviews. A line whose unit was not confirmed is left for the
        review, and the user is told how many."""
        skipped = self.env["l10n_br_fiscal.document.line"]
        for document in self:
            matched = document.fiscal_line_ids.filtered(
                lambda line: line.import_state == "matched"
            )
            skipped |= matched.filtered(lambda line: line._import_unit_unconfirmed())
            (matched - skipped).action_resolve_line()
        if not skipped:
            return True
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Some lines were not confirmed"),
                "message": _(
                    "%(count)s line(s) kept for the review: the unit declared by "
                    "the supplier has no match. Choose the unit of each one."
                )
                % {"count": len(skipped)},
                "type": "warning",
                "sticky": True,
                "next": {"type": "ir.actions.client", "tag": "reload"},
            },
        }

    def get_state_machine_config(self):
        config = super().get_state_machine_config()
        config["transitions"].append(
            {
                # Imported, issued by the company and authorized in another system
                # (a migration): only the state changes.
                "trigger": "action_confirm_imported",
                "source": DOCUMENT_STATE_DRAFT,
                "dest": DOCUMENT_STATE_AUTHORIZED,
            }
        )
        return config

    def action_document_confirm(self):
        """An imported document is confirmed only when every line was reviewed.

        One that the company issued in another system is already authorized there:
        it goes from draft to authorized in a transition of its own, which runs no
        callback: nothing is checked against the schema of issuing, exported,
        numbered, sent or turned into an event, and the number, the series, the XML
        and the protocol are the ones of the file.
        """
        drafts = self.filtered(
            lambda doc: doc.imported_document and doc.state_edoc == DOCUMENT_STATE_DRAFT
        )
        own = drafts.filtered(lambda doc: doc.issuer == DOCUMENT_ISSUER_COMPANY)
        for document in drafts:
            causes = []
            unresolved = document.fiscal_line_ids.filtered(
                lambda line: line.import_state in ("pending", "matched")
            )
            if unresolved:
                causes.append(
                    _(
                        "The document %(document)s has lines that were not reviewed:"
                        "\n%(lines)s"
                    )
                    % {
                        "document": document.display_name,
                        "lines": "\n".join(unresolved.mapped("name")),
                    }
                )
            if document in own and document.import_without_protocol:
                causes.append(
                    _(
                        "The file of %(document)s has no authorization protocol, so "
                        "it cannot be confirmed as authorized. Import the file with "
                        "the protocol."
                    )
                    % {"document": document.display_name}
                )
            if causes:
                # every cause at once: the person fixes them in one go
                raise UserError("\n\n".join(causes))
        for document in own:
            document._trigger_fsm("action_confirm_imported")
        return super(Document, self - own).action_document_confirm()
