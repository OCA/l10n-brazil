import datetime

import logging
from io import StringIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from lxml.builder import E


_logger = logging.getLogger(__name__)


LAYOUT_VERSIONS = {
    "ecd": "9",
    "ecf": "8",  # TODO 9 ?
    "efd_icms_ipi": "17",
    "efd_pis_cofins": "6",
}


class IrModel(models.Model):
    _inherit = "ir.model"

    # NOTE as we cannot let anyone edit Odoo models
    # these fields should be edited with a Wizard.
    sped_model_id = fields.Many2one("ir.model")
    sped_domain = fields.Char()


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    sped_mapping = fields.Char(
        help="Inform the field with the origin of the content, expressed with dot notation.",
    )


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
    res_model = fields.Char(string="Odoo Model")  # TODO compute_res_model using ir.model ?

    @api.depends("res_model", "res_id")
    def _compute_reference(self):
        for res in self:
            if not res.res_model:
                res.reference = ""
                continue
            model = self.env["ir.model"].search([("model", "=", self.res_model)])
            if not model:
                raise UserError(
                    _("Undefined mapping model for Register %s and model") % (self._name, self.res_model)
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
            if ": " in field["string"] and len(field["string"]) > 40:
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
            if ": " in field["string"] and len(field["string"]) > 40:
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
    def flush_registers(cls, kind="ecd", version=None):
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        register_classes = cls._get_level2_registers(kind, version)
        for register_class in register_classes:
            registers = register_class.search([])  # TODO company_id filter?
            registers.unlink()

    @api.model
    def import_file(cls, filename, kind="ecd", version=None):
        """
        ex:
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_efd_icms_ipi.txt", "efd_icms_ipi")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_efd_pis_cofins_multi.txt", "efd_pis_cofins")
        """
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        with open(filename) as spedfile:
            last_level = 0
            previous_register = None
            for line in [line.rstrip("\r\n") for line in spedfile]:
                reg_code = line.split("|")[1]
                version = LAYOUT_VERSIONS[kind]
                register_class = cls.env.get(
                    "l10n_br_sped.%s.%s.%s"
                    % (
                        kind,
                        version,
                        reg_code.lower(),
                    ),
                    None,
                )
                print("\nREF", reg_code, register_class)
                if register_class is None:
                    if "001" in reg_code or "990" in reg_code or reg_code == "9999":
                        continue
                    if reg_code in ("0000", "0007"):  # FIXME
                        continue
                    raise UserError(
                        _(
                            "Register %s doesn't match Odoo %s SPED structure version %s!"
                        )
                        % (reg_code, kind, version)
                    )

                if register_class._sped_level < 3:  # TODO if more than +1 -> error!
                    parents = []
                    parent = None
                    last_level = register_class._sped_level
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

                values = line.split("|")[2:][:-1]
                # TODO add specific method for ECD I550, I550 and I555 with LEIAUTE PARAMETRIZÁVEL
                # as seen with demo, it seem we should take the rest of the line and put it in the
                # RZ_CONT* text field!
                vals = {}
                for fname, field in register_class._fields.items():
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
    def generate_sped_text(cls, kind="ecd", version=None):
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        register_level2_classes = cls._get_level2_registers(kind, version)
        sped = StringIO()
        last_bloco = None
        bloco = None
        line_total = 0
        line_count = [
            0
        ]  # mutable register line_count https://stackoverflow.com/a/15148557
        register0 = cls.env["l10n_br_sped.%s.%s.0000" % (kind, version)]
        register0.search([]).generate_register_text(sped, line_count)
        for register_class in register_level2_classes:
            bloco = register_class._name[-4:][0].upper()
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
                sped.write("\n|%s001|0|" % (bloco,))
                line_count[0] += 1

            registers = register_class.search([])  # TODO filter with company_id?
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
        return sped.getvalue()

    def _get_level2_registers(cls, kind="ecd", version=None):
        if version is None:
            version = LAYOUT_VERSIONS[kind]
        register_model_names = list(
            filter(
                lambda x: "l10n_br_sped.%s.%s" % (kind, version) in x, cls.env.keys()
            )
        )
        register_level2_models = [
            cls.env[m] for m in register_model_names if cls.env[m]._sped_level == 2
        ]
        return sorted(
            register_level2_models,
            key=lambda x: x._name[-4:][0]
            == "0"  # hacky bloco ordering that just does the job
            and "a" + x._name[-4:]
            or x._name[-4:][0] == "9"
            and "d" + x._name[-4:]
            or x._name[-4:][0] == "1"
            and "c" + x._name[-4:]
            or "b" + x._name[-4:],
        )

    def generate_register_text(self, sped, line_count={}):
        code = self._name[-4:].upper()
        keys = [i[0] for i in self._fields.items()]
        if (
            not keys
        ):  # happend with ECD I550, I555 and I555 with "LEIAUTE PARAMETRIZÁVEL"
            keys = ["id"]  # BUT should not happen!
        vals_list = self.read(keys)
        for vals in vals_list:
            sped.write("\n|%s|" % (code,))
            line_count[0] += 1
            children = []
            should_break_next = False
            for k, v in vals.items():
                if k == "id":
                    continue
                if self._fields[k].type == "one2many":
                    children.append(
                        self.env[self._fields[k].comodel_name].search([("id", "in", v)])
                    )
                    should_break_next = True
                    continue # we assume it's the last register specific field
                elif should_break_next:  # if the register has a parent but no children
                    break
                elif self._fields[k].type == "many2one":
                    should_break_next = True # we assume the parent marks the end of register fields 
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
                        if v < 0.00001:
                            val = ""
                        elif v % 1 < 0.00001:
                            val = str(int(v))
                        else:
                            val = str(v)
                    else:
                        val = str(v)
                    sped.write(val + "|")

            children = sorted(children, key=lambda reg: reg._name)
            for child in children:
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
