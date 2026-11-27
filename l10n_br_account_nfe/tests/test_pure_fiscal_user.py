# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import re

from lxml import etree

from odoo.tests import Form, tagged

from odoo.addons import l10n_br_nfe
from odoo.addons.l10n_br_fiscal_edi.tests.common import KEY_1, EdiImportCase

FIXTURE = os.path.join(
    l10n_br_nfe.__path__[0], "tests", "nfe", "v4_00", "leiauteNFe", f"NFe{KEY_1}.xml"
)
FIXTURE_DEST = re.compile(rb"(<dest>\s*)<(?:CNPJ|CPF)>\d+</(?:CNPJ|CPF)>")


@tagged("post_install", "-at_install")
class TestPureFiscalUser(EdiImportCase):
    """A user with only the group Fiscal User works on an imported NF-e from the
    import to the confirmation, the way the web client does it: the action, then
    the read of every field of the form."""

    def _xml(self):
        with open(FIXTURE, "rb") as xml_file:
            content = xml_file.read()
        recipient = self.company.partner_id.cnpj_cpf_stripped
        return FIXTURE_DEST.sub(rb"\1<CNPJ>%s</CNPJ>" % recipient.encode(), content)

    def _reload(self):
        self.env.flush_all()
        self.env.invalidate_all()

    def _read_fields(self, records, arch):
        """The fields of a view and, for each x2many that has a sub view in it, the
        fields of that sub view read on its records, as the web client does."""
        names = set()
        for node in arch.xpath("./field"):
            name = node.get("name")
            if name not in records._fields:
                continue
            names.add(name)
            field = records._fields[name]
            if field.type in ("one2many", "many2many"):
                for sub_view in node.xpath("./tree | ./form | ./kanban"):
                    self._read_fields(records[name], sub_view)
        return records.read(sorted(names))

    def _read_the_form(self, document):
        arch = etree.fromstring(document.get_view(view_type="form")["arch"])
        return self._read_fields(document, arch.xpath("//form")[0])[0]

    def test_the_form_is_read_back_after_the_confirmation(self):
        user = self._fiscal_user("pure_fiscal_user", form_groups=True)
        # the web client does not disable the tracking
        model = self.Document.with_user(user).with_context(
            allowed_company_ids=self.company.ids, tracking_disable=False
        )
        documents, errors, _warnings = model._edi_import_files(
            [("nfe.xml", self._xml())]
        )
        self.assertFalse(errors)
        document = documents.with_user(user).with_context(
            allowed_company_ids=self.company.ids, tracking_disable=False
        )
        document.fiscal_operation_id = self.env.ref("l10n_br_fiscal.fo_compras")
        product = self.env["product.product"].create({"name": "Reviewed product"})
        document.fiscal_line_ids._apply_import_depara(
            product=product, uom=self.uom_unit
        )
        # what the web client does not have in memory it reads again, as the user
        self._reload()
        self._read_the_form(document)
        self._reload()
        # edit a field and save, as the form does
        with Form(document) as form:
            form.date_in_out = "2026-01-11 09:45:00"
        self._reload()

        document.action_document_confirm()

        self.assertEqual(document.state_edoc, "autorizada")
        self._reload()
        self._read_the_form(document)
