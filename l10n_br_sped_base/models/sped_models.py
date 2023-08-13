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
    "ecf": "8",  # TODO 9 ?
    "efd_icms_ipi": "17",
    "efd_pis_cofins": "6",
}

MAX_REGISTER_NAME = 40


class IrModel(models.Model):
    _inherit = "ir.model"

    # NOTE as we cannot let anyone edit Odoo models
    # these fields should be edited with a Wizard.
    sped_model = fields.Char()
    sped_domain = fields.Char()

    sped_kind = fields.Selection(
        selection=[
            ("ecd", "ECD"),
            ("efd_icms_ipi", "EFD ICMS IPI"),
            ("efd_pis_cofins", "EFD PIS COFINS"),
            ("ecf", "ECF"),
        ],
        string="Sped Kind",
        compute="_compute_sped_kind",
        store=True,
    )

    sped_alphanum_sequence = fields.Char(
        compute="_compute_sped_alphanum_sequence",
        store=True,
    )

    sped_ecd_mapping = fields.Text()
    sped_efd_icms_ipi_mapping = fields.Text()
    sped_efd_pis_cofins_mapping = fields.Text()
    sped_ecf_mapping = fields.Text()

    @api.depends("model")
    def _compute_sped_kind(self):
        for model in self:
            if model.model.startswith("l10n_br_sped."):
                sub_split = model.model.split("l10n_br_sped.")[1].split(".")
                if len(sub_split) == 3:
                    model.sped_kind = sub_split[0]
                else:
                    model.sped_kind = None
            else:
                model.sped_kind = None

    @api.depends("model", "sped_kind")
    def _compute_sped_alphanum_sequence(self):
        """
        Used to order the SPED register in the same order
        as in the SPED layout (so the register name alone won't cut it)
        """
        for model in self:
            if not model.sped_kind:
                self.sped_alphanum_sequence = None
                continue
            model.sped_alphanum_sequence = self.env[
                "l10n_br_sped.mixin"
            ]._get_alphanum_sequence(model.model)


class SpedMixin(models.AbstractModel):
    _name = "l10n_br_sped.mixin"
    _description = "base class for all registers"

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
        string="Reference",
        compute="_compute_reference",
        readonly=True,
        store=False,
    )
    res_model = fields.Char(
        string="Odoo Model"
    )  # TODO compute_res_model using ir.model ?

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
        if name in ("xsd_type", "sped_length", "sped_required", "sped_card"):
            return True
        else:
            return super()._valid_field_parameter(field, name)

    @api.model
    def _get_alphanum_sequence(self, model_name):
        """
        Used to order the SPED register in the same order
        as in the SPED layout (so the register name alone won't cut it)
        """
        key = model_name[-4:][0]
        if key == "0":
            return "a" + model_name[-4:]
        elif model_name[-4:][0] == "9":
            return "d" + model_name[-4:]
        elif model_name[-4:][0] == "1":
            return "c" + model_name[-4:]
        else:
            return "b" + model_name[-4:]

    # _sql_constraints = [
    #    should probably use a plpgsql FUNCTION see _auto_init
    #    ('res_id_not_null_if_from_odoo', "CHECK(...)",
    #     "res_id should point to an existing Odoo record!"),
    # ]

    #    def _auto_init(self):
    # define a FUNCTION similar to this to check model, res_id integrity:
    # CREATE OR REPLACE FUNCTION check_record_exists(table_name VARCHAR(255), res_id INT)
    # RETURNS BOOLEAN AS $$
    # BEGIN
    #   RETURN EXISTS (SELECT 1 FROM (SELECT tablename FROM pg_tables WHERE tablename = table_name) t WHERE t.id = res_id);
    # END;
    # $$ LANGUAGE plpgsql;

    @api.model
    def _get_default_tree_view(self):
        """Generates a single-field tree view, based on _rec_name.

        :returns: a tree view as an lxml document
        :rtype: etree._Element
        """
        desc = self._description
        tree = E.tree(string=desc)
        # required_fields_count = len([f[1] for f in self._fields.items() if f[1].required])
        fields = self.fields_get()

        added_fields = set()

        for fname, native_field in self._fields.items():
            # register fields: the 1st and the required ones
            if native_field.automatic or fname.endswith("brl_currency_id"):
                continue
            elif len(added_fields) > 0 and not native_field.required:
                continue
            elif not native_field.required:
                continue
            elif native_field.type == "many2one":
                continue
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
                native_field.automatic
                or fname.endswith("brl_currency_id")
                or fname in added_fields
                or native_field.type == "many2one"
            ):
                continue
            if len(added_fields) > 5:
                break

            field = fields[fname]
            if ": " in field["string"] and len(field["string"]) > MAX_REGISTER_NAME:
                string = field["string"].split(": ")[0]
            else:
                string = field["string"]

            added_fields.add(fname)
            tree.append(E.field(name=fname, string=string))

        return tree

    @api.model
    def _get_default_form_view(self):
        """Generates a default single-line form view using all fields
        Overriden to skip XSD fields that will be added later
        """
        group = E.group(col="4")
        for fname, field in self._fields.items():
            if field.automatic:
                continue
            if (
                fname.startswith("reg_")
                and fname.endswith("_id")
                and "_Registro" in fname
            ):  # inline m2o parent
                continue
            if fname.endswith("currency_id"):
                continue
            elif field.type in ("one2many", "many2many", "text", "html"):
                group.append(E.newline())
                group.append(E.field(name=fname, colspan="4"))
                group.append(E.newline())
            else:
                group.append(E.field(name=fname))
        group.append(E.separator())
        return E.form(E.sheet(group, string=self._description))

    @api.model
    def flush_registers(cls, kind):
        register_classes = cls._get_level2_registers(kind)
        for register_class in register_classes:
            registers = register_class.search([])  # TODO company_id filter?
            registers.unlink()

    @api.model
    def import_file(cls, filename, kind):
        """
        examples:
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped/demo/demo_efd_pis_cofins_multi.txt", "efd_pis_cofins")
        """
        with open(filename) as spedfile:
            last_level = 0
            previous_register = None
            parent = None
            parents = []
            for line in [line.rstrip("\r\n") for line in spedfile]:
                reg_code = line.split("|")[1]
                register_class = cls.env.get(
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
                    if reg_code in ("0000", "0007"):  # FIXME
                        continue
                    raise UserError(
                        _("Register %s doesn't match Odoo %s SPED structure!")
                        % (reg_code, kind)
                    )

                if register_class._sped_level < 3:  # TODO if more than +1 -> error!
                    last_level = register_class._sped_level
                    parent = None
                    parents = []
                elif (
                    register_class._sped_level > last_level
                ):  # TODO if more than +1 -> error!
                    parents.append(previous_register)
                    parent = parents[-1]
                    last_level = register_class._sped_level
                elif register_class._sped_level < last_level:
                    parents.pop()
                    parent = parents[-1]
                    last_level = register_class._sped_level

                vals = register_class.import_register(line)

                if parent:
                    vals[
                        "reg_%s_ids_Registro%s_id"
                        % (
                            register_class._name.split(".")[-1].upper(),
                            parent._name.split(".")[-1].upper(),
                        )
                    ] = parent.id
                register = register_class.create(vals)
                previous_register = register

    @api.model
    def import_register(cls, line):
        values = line.split("|")[2:][:-1]
        vals = {}
        for fname, field in cls._fields.items():
            if field.automatic or fname.endswith("currency_id"):
                continue
            if len(values) == 0:
                break
            if field.type in ("many2one", "one2many"):
                print(
                    "BAD REGISTER FIELDS!! more values than fields in Odoo!",
                    values,
                    fname,
                )
                break
            val = values.pop(0)

            if field.type == "integer":
                if val == "":
                    vals[fname] = 0
                else:
                    vals[fname] = int(val)

            elif field.type in ("float", "monetary"):
                if val == "":
                    vals[fname] = 0.0
                else:
                    vals[fname] = float(val.replace(",", "."))
            elif field.type == "date":
                if val != "":
                    vals[fname] = datetime.datetime.strptime(val, "%d%m%Y")
            else:
                vals[fname] = val
        return vals

    @api.model
    def generate_sped_text(cls, kind):
        register_level2_classes = cls._get_level2_registers(kind)
        sped = StringIO()
        last_bloco = None
        bloco = None
        line_total = 0
        line_count = [
            0
        ]  # mutable register line_count https://stackoverflow.com/a/15148557
        # domain = [("company_id", "=", company_id)]
        domain = []  # TODO put company_id and also date_field from register_class
        register0 = cls.env["l10n_br_sped.%s.0000" % (kind)]
        register0.search(domain).generate_register_text(sped, line_count)

        count_by_bloco = defaultdict(int)
        for register_class in register_level2_classes:
            bloco = register_class._name[-4:][0].upper()
            count_by_bloco[bloco] += register_class.search_count([])

        for register_class in register_level2_classes:
            bloco = register_class._name[-4:][0].upper()
            registers = register_class.search(domain)  # TODO filter with company_id?
            if bloco != last_bloco:
                if last_bloco:
                    sped.write(
                        "\n|%s990|%s|"
                        % (
                            last_bloco,
                            line_count[0] + 1,
                        )
                    )
                    line_total += line_count[0] + 1
                    line_count = [0]
                sped.write(
                    "\n|%s001|%s|" % (bloco, 0 if count_by_bloco[bloco] > 0 else 1)
                )
                line_count[0] += 1
                #            if registers:
                # print("RRRRRRRRRR", registers)
                # registers.visit_tree()
            registers.generate_register_text(sped, line_count)  # TODO use yield!
            last_bloco = bloco

        if (
            kind == "ecf"
        ):  # WTF why is it different?? You kidding me? or is it an error?
            sped.write("\n|" + bloco + "099|%s|" % (line_count[0] + 2,))
        else:
            sped.write("\n|" + bloco + "990|%s|" % (line_count[0] + 2,))
        line_total += line_count[0] + 2
        sped.write(
            "\n|9999|%s|" % (line_total,)
        )  # FIXME incorrect? error in test files?
        #        x = a / 0
        return sped.getvalue()

    @api.model
    def _get_level2_registers(cls, kind):
        """
        Get the "blocos" registers
        """
        register_model_names = list(
            filter(lambda x: "l10n_br_sped.%s" % (kind,) in x, cls.env.keys())
        )
        register_level2_models = [
            cls.env[m]
            for m in register_model_names
            if cls.env[m]._sped_level == 2 and not cls.env[m]._abstract
        ]
        return sorted(
            register_level2_models, key=lambda r: cls._get_alphanum_sequence(r._name)
        )

    @api.model
    def populate_sped_from_odoo(cls, kind):
        register0 = cls.env["l10n_br_sped.%s.0000" % (kind,)]
        register0.pull_records_from_odoo(level=1)

        for register in cls._get_level2_registers(
            kind,
        ):
            register.pull_records_from_odoo(level=2)

    @api.model
    def pull_records_from_odoo(cls, level, parent_record=None):
        model = cls.env["ir.model"].search([("model", "=", cls._name)], limit=1)
        # TODO see how it fits with ATSTI stuff
        if not model.sped_model:
            return
        children = [
            v["relation"]
            for k, v in cls.fields_get().items()
            if v["type"] == "one2many"
        ]
        records = cls.env[model.sped_model].search(model.sped_domain or [])
        _logger.debug("pulling register %s%s" % ("  " * level, self._name[-4:].upper()))
        for record in records:
            cls.import_from_odoo(record, parent_record)
            for child in children:
                print("ccc", child)
                cls.env[child].pull_records_from_odoo(level + 1, parent_record=record)

    @api.model
    def import_from_odoo(cls, record, parent_record):
        pass
        # TODO apply server action mapping
        # TODO check if not already imported

    def generate_register_text(self, sped, line_count={}):
        code = self._name[-4:].upper()
        keys = [i[0] for i in self._fields.items()]
        if (
            not keys
        ):  # happens with ECD I550, I555 and I555 with "LEIAUTE PARAMETRIZÁVEL"
            keys = ["id"]  # BUT should not happen!
        vals_list = self.read(keys)
        for vals in vals_list:
            sped.write("\n|%s|" % (code,))
            line_count[0] += 1
            children = []
            should_break_next = False
            #    yield code#, vals
            for k, v in vals.items():
                if k == "id":
                    continue
                if self._fields[k].type == "one2many":
                    children.append(
                        self.env[self._fields[k].comodel_name].search([("id", "in", v)])
                    )
                    should_break_next = True
                    continue  # we assume it's the last register specific field
                elif should_break_next:  # if the register has a parent but no children
                    break
                elif self._fields[k].type == "many2one":
                    should_break_next = (
                        True  # we assume the parent marks the end of register fields
                    )
                else:
                    if self._fields[k].type == "date":
                        if v:
                            val = v.strftime("%d%m%Y")
                        else:
                            val = ""
                    elif self._fields[k].type == "char":
                        if not v:
                            val = ""
                        else:
                            val = str(v)

                    elif self._fields[k].type == "integer":
                        if v == 0:
                            # NOTE not always what is done, ex ECD I510 DEC_CAMPO
                            # TODO what do we do?
                            # 1) find a better heuristic?
                            # 2) specific override?
                            # 3) change test/demo file if it's OK?
                            val = ""
                        else:
                            val = str(v)
                    elif self._fields[k].type == "float":
                        if v % 1 < 0.00001:  # ex: aliquota ICMS
                            val = str(int(v))
                        else:
                            val = str(v).replace(".", ",")
                    elif self._fields[k].type == "monetary":
                        if float_is_zero(v, precision_digits=8):
                            val = ""
                        elif float_is_zero(v % 1, precision_digits=8):
                            val = str(int(v))
                        else:
                            val = str(v)
                    else:
                        val = str(v)
                    sped.write(val + "|")

            children = sorted(children, key=lambda reg: reg._name)
            for child in children:
                #    yield from child.generate_register_text(sped, line_count)  # NOTE use yield?
                child.generate_register_text(sped, line_count)  # NOTE use yield?
        return sped

        # ==== MAPPING EDITION ====

        def action_edit_mappings(self):
            pass  # TODO use a specific wizard

        def action_export_all_mappings(self):
            pass  # TODO use a specific wizard

        def action_load_mappings_file(self):
            pass  # TODO use a specific wizard

        # ==== RECORD MAPPING ====

        def import_for_all_register(self, kind, version):
            pass
            # TODO collect all the registers and call import_from_odoo
            # on them

        def import_from_odoo(self, domain=None):
            """Used in Odoo transaction to create the SPED registers"""
            model = self.env["ir.model"].search([("name", "=", self.model)])
            if not model:
                raise UserError(
                    _("Undefined mapping model for Register %s") % (self._name,)
                )
            domain = domain or model.sped_domain
            records = self.env[model.model].search(domain)
            for rec in records:
                pass

            # TODO mapp fields with dot notation like for the CNAB:


#            value = rec.default_value or ""
#            if rec.content_source_field and resource_ref:
#                value = (
#                    operator.attrgetter(rec.content_source_field)(resource_ref) or ""
#                )
#            if rec.sending_dynamic_content:
#                value = rec.eval_compute_value(
#                    value, rec.sending_dynamic_content, **kwargs
#                )
#            value = self.format(rec.size, rec.type, value)
#            return self.ref_name, value
