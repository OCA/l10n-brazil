# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import datetime
import logging
from collections import defaultdict
from io import StringIO

from lxml.builder import E

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

LAYOUT_VERSIONS = {
    "ecd": "9",
    "ecf": "9",
    "efd_icms_ipi": "17",
    "efd_pis_cofins": "6",
    "fake": "9",  # tests; similar to ecd
}

MAX_REGISTER_NAME = 40

EDITABLE_ON_DRAFT = "{'readonly': [('state', 'not in', ['draft'])]}"


class SpedMixin(models.AbstractModel):
    _name = "l10n_br_sped.mixin"
    _description = "base class for all registers"
    _odoo_model = None

    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    brl_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Moeda",
        compute="_compute_currency_id",
        default=lambda self: self.env.ref("base.BRL").id,
    )

    is_imported = fields.Boolean()
    is_generated_from_odoo = fields.Boolean()

    res_id = fields.Many2oneReference(
        string="Record ID",
        help="ID of the target record in the database",
        model_field="res_model",
    )
    reference = fields.Char(
        string="Odoo Reference",
        compute="_compute_reference",
        readonly=True,
        store=False,
    )
    res_model = fields.Char(string="Odoo Model")

    @api.depends("res_model", "res_id")
    def _compute_reference(self):
        for res in self:
            if not res.res_model:
                res.reference = ""
                continue
            model = self.env["ir.model"].search([("model", "=", res.res_model)])
            if not model:
                raise UserError(
                    _(
                        "Undefined mapping model for Register "
                        "%(name)s and model %(model)s",
                        name=self._name,
                        model=self.res_model,
                    )
                )
            res.reference = f"{model.model},{res.res_id}"

    def _compute_currency_id(self):
        for item in self:
            item.brl_currency_id = self.env.ref("base.BRL").id

    def _valid_field_parameter(self, field, name):
        if name in (
            "xsd_type",
            "sped_length",
            "sped_required",
            "sped_card",
            "in_required",
            "out_required",
        ):
            return True
        else:
            return super()._valid_field_parameter(field, name)

    @api.model
    def _odoo_domain(self, parent_record, declaration):
        return []

    @api.model
    def _get_alphanum_sequence(self, model_name):
        """
        Helper method to get alphanumeric sequence for sorting registers.
        (the register name alone won't cut it)
        """
        register_code = model_name[-4:]
        bloco_key = register_code[0]
        if bloco_key == "0":
            return "0" + register_code
        elif bloco_key == "1":
            return "2" + register_code
        elif bloco_key == "9":
            return "3" + register_code
        else:
            return "1" + register_code

    @api.model
    def _get_top_registers(self, kind):
        """
        Get the top register classes, the "blocos", for a specific kind.

        :param kind: Type of SPED register
        :return: List of top register classes
        """

        register_model_names = list(
            filter(lambda x: f"l10n_br_sped.{kind}" in x, self.env.keys())
        )
        register_level2_models = [
            self.env[m]
            for m in register_model_names
            if not self.env[m]._abstract and self.env[m]._sped_level == 2
        ]
        return sorted(
            register_level2_models, key=lambda r: self._get_alphanum_sequence(r._name)
        )

    @api.model
    def _get_default_tree_view(self):
        """Generate a single-field tree view, based on _rec_name.

        :return: a tree view as an lxml document
        :rtype: etree._Element
        """
        desc = self._description
        tree = E.tree(string=desc)
        fields = self.fields_get()
        added_fields = set()

        tree.append(E.field(name="state", invisible="1"))
        if not self._name.endswith("0000"):
            tree.append(E.field(name="declaration_id"))

        for fname, native_field in self._ordered_fields():
            # register fields: the 1st and the required ones
            if not fname.isupper():
                continue
            elif len(added_fields) > 0 and not native_field.required:
                continue
            elif not native_field.required:
                continue
            elif native_field.type == "many2one":
                continue
            if len(added_fields) > 6:
                break

            field = fields[fname]
            if ": " in field["string"] and len(field["string"]) > MAX_REGISTER_NAME:
                string = field["string"].split(": ")[0]
            else:
                string = field["string"]

            added_fields.add(fname)
            tree.append(E.field(name=fname, string=string))

        for fname, native_field in self._ordered_fields():
            # the register o2m/o2o children:
            if (
                fname in added_fields
                or native_field.type == "many2one"
                or not fname.isupper()
            ):
                continue
            if len(added_fields) > 6:
                break

            field = fields[fname]
            if ": " in field["string"] and len(field["string"]) > MAX_REGISTER_NAME:
                string = field["string"].split(": ")[0]
            else:
                string = field["string"]

            added_fields.add(fname)
            tree.append(E.field(name=fname, string=string))

        all_sped_fields = [
            fname
            for fname, native_field in self._fields.items()
            if (fname.isupper() and native_field.type != "many2one")
            or native_field.type == "one2many"
        ]
        if len(added_fields) == len(all_sped_fields):
            tree.attrib["editable"] = "bottom"
        return tree

    @api.model
    def _get_view(self, view_id=None, view_type="form", **options):
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type != "form":
            return arch, view

        group = E.group(col="4")
        self._append_top_view_elements(group)
        group.append(E.field(name="state", invisible="1"))

        for fname, field in self._ordered_fields():
            if field.automatic:
                continue
            if field.type == "many2one" and "_Registro" in fname:  # inline m2o parent
                continue
            if fname.endswith("currency_id"):
                continue
            if not fname.isupper() and (
                # skip mail.thread fields
                fname != "declaration_id" and not fname.startswith("reg_")
            ):
                continue
            elif field.type in ("one2many", "many2many", "text", "html"):
                group.append(E.newline())
                field_tag = E.field(
                    name=fname,
                    colspan="4",
                    attrs=EDITABLE_ON_DRAFT,
                    context="{'default_declaration_id': declaration_id}",
                )
                if field.type == "one2many":
                    tree_fields = [
                        (f, native_field)
                        for f, native_field in self.env[
                            field.comodel_name
                        ]._fields.items()
                        if (f.isupper() or f.startswith("reg_"))
                        and native_field.type != "many2one"
                    ]
                    if len(tree_fields) < 5 and not any(
                        (
                            tree_field[0].startswith("reg_")
                            and tree_field[1].type == "one2many"
                        )
                        for tree_field in tree_fields
                    ):
                        # few fields -> editable tree
                        field_tree = E.tree(editable="bottom")
                        field_tree.append(E.field(name="declaration_id", invisible="1"))
                        field_tree.append(E.field(name="state", invisible="1"))
                        field_tree.append(E.field(name="reference", widget="reference"))
                        for tree_field in tree_fields:
                            field_tree.append(
                                E.field(
                                    name=tree_field[0],
                                )
                            )
                        field_tag.append(field_tree)
                    else:
                        field_tree = E.tree()
                        field_tree.append(E.field(name="state", invisible="1"))
                        for index, tree_field in enumerate(tree_fields):
                            if index > 6:
                                break
                            if (
                                tree_field[0].startswith("reg_")
                                and tree_field[1].type == "one2many"
                            ):
                                continue
                            field_tree.append(
                                E.field(
                                    name=tree_field[0],
                                    string=tree_field[0],
                                )
                            )
                        field_tag.append(field_tree)
                        field_form = self.env[
                            field.comodel_name
                        ]._get_default_form_view()  # inline=True)
                        field_tag.append(field_form)
                group.append(field_tag)
                group.append(E.newline())
            elif fname.isupper():
                group.append(E.field(name=fname, attrs=EDITABLE_ON_DRAFT))
        group.append(E.separator())
        form = E.form()
        self._append_view_header(form)
        form.append(E.sheet(group, string=self._description))
        self._append_view_footer(form)
        return form, view

    @api.model
    def _append_view_header(self, form):
        pass

    @api.model
    def _append_view_footer(self, form):
        pass

    @api.model
    def _append_top_view_elements(self, group, inline=False):
        group.append(
            E.field(
                name="declaration_id",
                attrs=(
                    "{'readonly': "
                    "[('state', 'not in', ['draft']), "
                    "('declaration_id', '!=', False)]}"
                ),
                invisible="1" if inline else "0",
            )
        )
        group.append(E.field(name="reference", widget="reference"))
        group.append(E.separator(colspan="4"))

    @api.model
    def _flush_registers(self, kind, declaration_id=None):
        """
        Flush the SPED registers for a specific kind and declaration.

        :param kind: Type of SPED register
        :param declaration_id: Declaration ID to flush
        """
        if declaration_id:
            domain = [("declaration_id", "=", declaration_id)]
        else:
            domain = []

        register_classes = self._get_top_registers(kind)
        for register_class in register_classes:
            registers = register_class.search(domain)
            registers.unlink()

    @api.model
    def _import_file(self, filename, kind, version=None, declaration=None):
        """
        Import SPED files into Odoo.

        :param filename: Path to the SPED file.
        :param kind: Type of SPED file (e.g., "ecd", "efd_pis_cofins").
        :param version: SPED layout version (optional).
        :return: Declaration record created in Odoo.

        examples:
        env["l10n_br_sped.mixin"]._import_file(
            "/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd"
        )
        env["l10n_br_sped.mixin"]._import_file(
            "/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd"
        )
        env["l10n_br_sped.mixin"]._import_file(
            "/odoo/links/l10n_br_sped/demo/demo_efd_pis_cofins_multi.txt",
            "efd_pis_cofins",
        )
        """
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        with open(filename) as spedfile:
            last_level = 0
            previous_register = None
            parent = None
            parents = []
            level_2_registers = defaultdict(list)
            for line in [line.rstrip("\r\n") for line in spedfile]:
                reg_code = line.split("|")[1]

                if declaration is not None and reg_code == "0000":
                    continue
                register_class = self.env.get(
                    f"l10n_br_sped.{kind}.{reg_code.lower()}",
                    None,
                )

                if register_class is None:
                    if "001" in reg_code or "990" in reg_code or reg_code == "9999":
                        continue
                    raise UserError(
                        _(
                            "Register %(code)s doesn't match "
                            "Odoo %(kind)s SPED structure!",
                            code=reg_code,
                            kind=kind,
                        )
                    )

                if register_class._sped_level < 3:  # TODO if more than +1 -> error!
                    last_level = register_class._sped_level
                    parent = None
                    parents = []
                elif register_class._sped_level > last_level:
                    parents.append(previous_register)
                    parent = parents[-1]
                    last_level = register_class._sped_level
                elif register_class._sped_level < last_level:
                    parents.pop()
                    parent = parents[-1]
                    last_level = register_class._sped_level

                vals = register_class._read_register_line(line, version)
                if declaration is not None:
                    vals["declaration_id"] = declaration.id

                if parent:
                    register = register_class._name.split(".")[-1].upper()
                    parent_code = parent._name.split(".")[-1].upper()
                    vals[f"reg_{register}_ids_Registro{parent_code}_id"] = parent.id
                register = register_class.create(vals)
                if reg_code == "0000":
                    declaration = register
                if register_class._sped_level == 2:
                    level_2_registers[reg_code].append(register)

                previous_register = register

        log_msg = StringIO()
        log_msg.write(f"<h3>{_('Imported from file:')}</h3>")
        for _code, registers in level_2_registers.items():
            registers[0]._log_chatter_sped_item(log_msg, 2, registers)
        declaration.message_post(body=log_msg.getvalue())

        return declaration

    @api.model
    def _ordered_fields(self):
        """class _fields in the order they are declared."""
        code = self._name.split(".")[-1].upper()
        register_class = next(
            filter(
                lambda c: c.__name__ == f"Registro{code}", reversed(type(self).mro())
            )
        )
        fields = []
        for name in register_class.__dict__.keys():
            if name in self._fields:
                fields.append((name, self._fields[name]))

        return fields

    @api.model
    def _read_register_line(self, line, version):
        """
        Read a single SPED register line and convert it into Odoo record values.

        :param line: SPED register line.
        :param version: SPED layout version.
        :return: Dictionary of field values.
        """

        values = line.split("|")[2:][:-1]
        register_vals = {"is_imported": True}
        code = self._name[-4:]
        register_spec_model = self._name.replace(f".{code}", f".{version}.{code}")
        register_spec = self.env[register_spec_model]
        _logger.info(f"register_spec: {register_spec}, reading {line}")
        for fname, field in register_spec._ordered_fields():
            if not fname[0].isupper():  # Skip non-SPED fields
                continue
            if not values:
                break
            if field.type in ("many2one", "one2many"):
                raise RuntimeError(
                    "Bad register fields! more values "
                    f"than fields in Odoo! {fname} {values}"
                )
            val = values.pop(0)

            if field.type == "integer":
                register_vals[fname] = int(val) if val else 0
            elif field.type in ("float", "monetary"):
                register_vals[fname] = float(val.replace(",", ".")) if val else 0.0
            elif field.type == "date":
                register_vals[fname] = (
                    datetime.datetime.strptime(val, "%d%m%Y") if val else None
                )
            else:
                register_vals[fname] = val
        return register_vals

    def _generate_register_text(self, sped, version, line_count, count_by_register):
        """
        Recursively generate the SPED text for a register.

        :param sped: StringIO object to write SPED text
        :param version: Layout version
        :param line_count: Line count list
        :param count_by_register: Dictionary to count registers
        """
        code = self._name[-4:].upper()
        register_spec_model = self._name.replace(
            f".{code.lower()}", f".{version}.{code.lower()}"
        )
        register_spec = self.env[register_spec_model]
        keys = [k for k, v in register_spec._ordered_fields()] or ["id"]

        if len(self):
            count_by_register[code] += len(self)

        for rec in self:
            self._write_register_line(sped, code, rec, keys, line_count, register_spec)
            self._process_children(
                sped, version, line_count, count_by_register, rec, keys, register_spec
            )
        return sped

    def _write_register_line(self, sped, code, rec, keys, line_count, register_spec):
        """
        Write a line for the register.

        :param sped: StringIO object to write SPED text
        :param code: Register code
        :param rec: Record
        :param keys: List of field keys
        :param line_count: Line count list
        :param register_spec: Register specification model
        """
        line_start = "" if code == "0000" else "\n"
        sped.write(f"{line_start}|{code}|")
        line_count[0] += 1

        for fname, value in {k: getattr(rec, k) for k in keys}.items():
            if not fname.isupper():
                continue

            val = self._format_field_value(register_spec._fields[fname], value)
            sped.write(f"{val}|")

    def _format_field_value(self, field, value):
        """
        Format the field value based on its type.

        :param field: Field object
        :param value: Field value
        :return: Formatted field value as string
        """
        if field.type == "date":
            return value.strftime("%d%m%Y") if value else ""
        elif field.type == "char" or field.type == "selection":
            return str(value) if value else ""
        elif field.type == "integer":
            return "" if value == 0 else str(value)
        elif field.type == "float":
            return (
                str(int(value))
                if float_is_zero(value % 1, 6)
                else str(round(value, 6)).replace(".", ",")
            )
        elif field.type == "monetary":  # TODO is is usefull? (not used now)
            return (
                ""
                if float_is_zero(value, precision_digits=8)
                else (
                    str(int(value))
                    if float_is_zero(value % 1, precision_digits=8)
                    else str(value)
                )
            )
        else:
            return str(value)

    def _process_children(
        self, sped, version, line_count, count_by_register, rec, keys, register_spec
    ):
        """
        Process child registers recursively.

        :param sped: StringIO object to write SPED text
        :param version: Layout version
        :param line_count: Line count list
        :param count_by_register: Dictionary to count registers
        :param rec: Record
        :param keys: List of field keys
        :param register_spec: Register specification model
        """
        children_groups = [
            getattr(rec, fname)
            for fname in keys
            if register_spec._fields[fname].type == "one2many"
            and fname.startswith("reg_")
        ]
        for children in sorted(children_groups, key=lambda c: c._name):
            children._generate_register_text(
                sped, version, line_count, count_by_register
            )

    @api.model
    def _pull_records_from_odoo(
        self, kind, level, parent_register=None, parent_record=None, log_msg=None
    ):
        """
        Pull records from Odoo and populate the SPED registers.

        :param kind: Type of SPED register
        :param level: Depth level for pulling records
        :param parent_register: Parent register if any
        :param parent_record: Parent record if any
        :param log_msg: StringIO object for logging
        """
        declaration = self._context["declaration"]

        children = [
            v["relation"]
            for k, v in self.fields_get().items()
            if v["type"] == "one2many" and k.startswith("reg_")
        ]
        parent_field = None
        if parent_register:
            parent_field = [
                k
                for k, v in self.fields_get().items()
                if v["type"] == "many2one"
                and k.startswith("reg_")
                and k.endswith("_id")
            ][0]

        if self._odoo_model and hasattr(self, "_odoo_domain"):
            records = self.env[self._odoo_model].search(
                self._odoo_domain(parent_record, declaration)
            )

        elif hasattr(self, "_odoo_query"):
            self._cr.execute(*self._odoo_query(parent_record, declaration))
            records = self._cr.dictfetchall()

        elif hasattr(self, "_map_from_odoo"):
            # in this case we will generate a register without any
            # specific Odoo record. Example: ECD I010
            register_vals = self._map_from_odoo(None, parent_record, declaration)
            if parent_register:
                register_vals[parent_field] = parent_register.id
            register = self.create(register_vals)
            for child in children:
                self.env[child]._pull_records_from_odoo(
                    kind,
                    level + 1,
                    parent_register=register,
                    parent_record=None,
                    log_msg=log_msg,
                )
            self._log_chatter_sped_item(log_msg, level, [register])
            return

        else:
            self._log_chatter_sped_item(log_msg, level)
            return

        self._log_chatter_sped_item(log_msg, level, records)

        for index, record in enumerate(records):
            # TODO find a way/mode to skip pulling existing records
            # may be search for existing register with res_model/res_id
            # or even parent_field and skip
            register_vals = self._map_from_odoo(
                record, parent_record, declaration, index=index
            )
            if self._odoo_model:
                register_vals["res_model"] = self._odoo_model
                register_vals["res_id"] = record.id
            if parent_register:
                register_vals[parent_field] = parent_register.id
            register = self.create(register_vals)

            for child in children:
                self.env[child]._pull_records_from_odoo(
                    kind,
                    level + 1,
                    parent_register=register,
                    parent_record=record,
                    log_msg=log_msg,
                )

    @api.model
    def _log_chatter_sped_item(self, log_msg, level, records=None):
        action = self.env["ir.actions.act_window"].search(
            [("res_model", "=", self._name)], limit=1
        )
        if action:
            record_count = f" ({len(records)} records)" if records else ""
            body = (
                f"<div>{'&nbsp;' * level * 4}"
                f'<a href="/web#action={action.id}" >'
                f"{self._name[-4:].upper()}{record_count}</a></div>"
            )
            log_msg.write(body)
