# Copyright 2023 - TODAY, Akretion - Raphael Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).

import datetime

from lxml.builder import E

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

LAYOUT_VERSIONS = {
    "ecd": "9",
    "ecf": "9",
    "efd_icms_ipi": "17",
    "efd_pis_cofins": "6",
}

MAX_REGISTER_NAME = 40


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
            model = self.env["ir.model"].search([("model", "=", self.res_model)])
            if not model:
                raise UserError(
                    _("Undefined mapping model for Register %s and model")
                    % (self._name, self.res_model)
                )
            res.reference = "%s,%s" % (model.model, res.res_id)

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
    def _odoo_domain(self):
        return []

    @api.model
    def _get_alphanum_sequence(self, model_name):
        """
        Used to order the SPED register in the same order
        as in the SPED layout (the register name alone won't cut it)
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
        Get the "blocos" registers
        """
        register_model_names = list(
            filter(lambda x: "l10n_br_sped.%s" % (kind,) in x, self.env.keys())
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
        if not self._name.endswith("0000"):
            tree.append(E.field(name="declaration_id"))

        for fname, native_field in self._fields.items():
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

        for fname, native_field in self._fields.items():
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
    def _get_default_form_view(self):
        """Generate a default single-line form view using all fields

        :return: a tree view as an lxml document
        :rtype: etree._Element
        """
        group = E.group(col="4")
        self._append_top_view_elements(group)

        for fname, field in self._fields.items():
            if field.automatic:
                continue
            if field.type == "many2one" and "_Registro" in fname:  # inline m2o parent
                continue
            if fname.endswith("currency_id"):
                continue
            if not fname.isupper() and (
                # skip mail.thread fields
                fname != "declaration_id"
                and not fname.startswith("reg_")
            ):
                continue
            elif field.type in ("one2many", "many2many", "text", "html"):
                group.append(E.newline())
                field_tag = E.field(name=fname, colspan="4")
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
                        for tree_field in tree_fields:
                            field_tree.append(E.field(name=tree_field[0]))
                        field_tag.append(field_tree)
                    else:
                        field_tree = E.tree()
                        for index, tree_field in enumerate(tree_fields):
                            if index > 6:
                                break
                            if (
                                tree_field[0].startswith("reg_")
                                and tree_field[1].type == "one2many"
                            ):
                                continue
                            field_tree.append(
                                E.field(name=tree_field[0], string=tree_field[0])
                            )
                        field_tag.append(field_tree)
                group.append(field_tag)
                group.append(E.newline())
            elif fname.isupper():
                group.append(E.field(name=fname))
        group.append(E.separator())
        form = E.form()
        self._append_view_header(form)
        form.append(E.sheet(group, string=self._description))
        self._append_view_footer(form)
        return form

    @api.model
    def _append_view_header(self, form):
        pass

    @api.model
    def _append_view_footer(self, form):
        pass

    @api.model
    def _append_top_view_elements(self, group):
        group.append(E.field(name="declaration_id", required="True"))
        group.append(E.field(name="reference", widget="reference"))
        group.append(E.separator(colspan="4"))

    @api.model
    def flush_registers(self, kind, declaration_id=None):
        if declaration_id:
            domain = [("declaration_id", "=", declaration_id)]
        else:
            domain = []

        register_classes = self._get_top_registers(kind)
        for register_class in register_classes:
            registers = register_class.search(domain)
            registers.unlink()

    @api.model
    def import_file(self, filename, kind, version=None):
        """
        Import SPED files into Odoo.

        :param filename: Path to the SPED file.
        :param kind: Type of SPED file (e.g., "ecd", "efd_pis_cofins").
        :param version: SPED layout version (optional).
        :return: Declaration record created in Odoo.

        examples:
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_efd_pis_cofins_multi.txt", "efd_pis_cofins")
        """
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        with open(filename) as spedfile:
            last_level = 0
            previous_register = None
            parent = None
            parents = []
            declaration = None
            for line in [line.rstrip("\r\n") for line in spedfile]:
                reg_code = line.split("|")[1]
                register_class = self.env.get(
                    "l10n_br_sped.%s.%s"
                    % (
                        kind,
                        reg_code.lower(),
                    ),
                    None,
                )
                if register_class is None:
                    if "001" in reg_code or "990" in reg_code or reg_code == "9999":
                        continue
                    raise UserError(
                        _("Register %s doesn't match Odoo %s SPED structure!")
                        % (reg_code, kind)
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

                vals = register_class.read_register_line(line, version)
                if declaration is not None:
                    vals["declaration_id"] = declaration.id

                if parent:
                    vals[
                        "reg_%s_ids_Registro%s_id"
                        % (
                            register_class._name.split(".")[-1].upper(),
                            parent._name.split(".")[-1].upper(),
                        )
                    ] = parent.id
                register = register_class.create(vals)
                if reg_code == "0000":
                    declaration = register
                previous_register = register

        return declaration

    @api.model
    def read_register_line(self, line, version):
        """
        Read a single SPED register line and convert it into Odoo record values.

        :param line: SPED register line.
        :param version: SPED layout version.
        :return: Dictionary of field values.
        """

        values = line.split("|")[2:][:-1]
        register_vals = {"is_imported": True}
        code = self._name[-4:]
        register_spec_model = self._name.replace(
            ".%s" % (code), ".%s.%s" % (version, code)
        )
        register_spec = self.env[register_spec_model]
        for fname, field in register_spec._fields.items():
            if not fname[0].isupper():  # Skip non-SPED fields
                continue
            if not values:
                break
            if field.type in ("many2one", "one2many"):
                raise RuntimeError(
                    "Bad register fields! more values than fields in Odoo! %s %s"
                    % (fname, values),
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

    # flake8: noqa: C901
    def generate_register_text(self, sped, version, line_count, count_by_register):
        """
        Recursively generate the SPED text of the registers.
        """
        code = self._name[-4:]
        register_spec_model = self._name.replace(
            ".%s" % (code), ".%s.%s" % (version, code)
        )
        code = code.upper()
        register_spec = self.env[register_spec_model]
        keys = [i[0] for i in register_spec._fields.items()]
        if (
            not keys
        ):  # happens with ECD I550, I555 and I555 with "LEIAUTE PARAMETRIZÁVEL"
            keys = ["id"]  # BUT should not happen!
        if len(self):
            count_by_register[code] += len(self)
        if code == "0000":
            line_start = ""
        else:
            line_start = "\n"
        for vals in self.read(keys):
            sped.write("%s|%s|" % (line_start, code))
            line_count[0] += 1
            children = []
            should_break_next = False
            for fname, value in vals.items():
                if register_spec._fields[fname].type == "one2many" and fname.startswith(
                    "reg_"
                ):
                    children.append(
                        self.env[self._fields[fname].comodel_name].search(
                            [("id", "in", value)]
                        )
                    )
                    should_break_next = True
                    continue  # we assume it's the last register specific field
                elif should_break_next:  # if the register has a parent but no children
                    break
                elif not fname.isupper():  # not a SPED field
                    continue

                # Handle different field types
                if self._fields[fname].type == "date":
                    val = value.strftime("%d%m%Y") if value else ""
                elif self._fields[fname].type == "char":
                    val = str(value) if value else ""
                elif self._fields[fname].type == "selection":
                    val = value if value else ""
                elif self._fields[fname].type == "integer":
                    if value == 0:
                        val = ""
                    else:
                        val = str(value)
                elif self._fields[fname].type == "float":
                    if float_is_zero(value % 1, 6):  # ex: aliquota ICMS
                        val = str(int(value))
                    else:
                        val = str(value).replace(".", ",")
                elif self._fields[fname].type == "monetary":
                    if float_is_zero(value, precision_digits=8):
                        val = ""
                    elif float_is_zero(value % 1, precision_digits=8):
                        val = str(int(value))
                    else:
                        val = str(value)

                else:
                    val = str(value)
                sped.write(val + "|")

            children = sorted(children, key=lambda reg: reg._name)
            for child in children:
                child.generate_register_text(
                    sped, version, line_count, count_by_register
                )
        return sped

    @api.model
    def pull_records_from_odoo(
        self, kind, level, parent_register=None, parent_record=None, log_msg=None
    ):
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
                self.env[child].pull_records_from_odoo(
                    kind,
                    level + 1,
                    parent_register=register,
                    parent_record=None,
                    log_msg=log_msg,
                )
            self.log_chatter_sped_item(log_msg, level, [register])
            return
        else:
            self.log_chatter_sped_item(log_msg, level)
            return

        self.log_chatter_sped_item(log_msg, level, records)

        for index, record in enumerate(records):
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
                self.env[child].pull_records_from_odoo(
                    kind,
                    level + 1,
                    parent_register=register,
                    parent_record=record,
                    log_msg=log_msg,
                )

    @api.model
    def log_chatter_sped_item(self, log_msg, level, records=None):
        actions = self.env["ir.actions.act_window"].search(
            [("res_model", "=", self._name)]
        )
        if actions:
            body = """
            <div>%s<a href="/web#action=%s" class="o_mail_redirect"
            target="_blank">%s%s</a></div>
            """ % (
                "&nbsp;" * level * 4,
                actions[0].id,
                self._name[-4:].upper(),
                records and " (%s records)" % (str(len(records)),) or "",
            )
            log_msg.write(body)
