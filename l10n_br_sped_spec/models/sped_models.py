import datetime

import logging
from io import StringIO
from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml.builder import E


_logger = logging.getLogger(__name__)


LAYOUT_VERSIONS = {
    "ecd": "9",                         
    "ecf": "8",
    "efd_icms_ipi": "17",
    "efd_pis_cofins": "6",
}


class SpedMixin(models.AbstractModel):
    _name = "l10n_br_sped.mixin"
    _description = "base class for all registers"

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        default=lambda self: self.env.company
    )

    brl_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moeda',
        compute='_compute_currency_id',
        default=lambda self: self.env.ref('base.BRL').id,
    )

    def _compute_currency_id(self):
        for item in self:
            item.brl_currency_id = self.env.ref('base.BRL').id

    def _valid_field_parameter(self, field, name):
        if name in ("xsd_type", "sped_length", "sped_required", "sped_card"):
            return True
        else:
            return super()._valid_field_parameter(field, name)

    @api.model
    def _get_default_tree_view(self):
        """ Generates a single-field tree view, based on _rec_name.

        :returns: a tree view as an lxml document
        :rtype: etree._Element
        """
        desc = self._description
        tree = E.tree(string=desc)
        required_fields_num = len([f[1] for f in self._fields.items() if f[1].required])
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
            if native_field.automatic or fname.endswith("brl_currency_id") or fname in added_fields or native_field.type == "many2one":
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
        """ Generates a default single-line form view using all fields
        Overriden to skip XSD fields that will be added later
        """
        group = E.group(col="4")
        for fname, field in self._fields.items():
            if field.automatic:
                continue
            if fname.startswith("reg_") and fname.endswith("_id") and "_Registro" in fname:  # inline m2o parent
                continue
            if fname.endswith("currency_id"):
                continue
            elif field.type in ('one2many', 'many2many', 'text', 'html'):
                group.append(E.newline())
                group.append(E.field(name=fname, colspan="4"))
                group.append(E.newline())
            else:
                group.append(E.field(name=fname))
        group.append(E.separator())
        return E.form(E.sheet(group, string=self._description))

    @api.model
    def empty_registers(cls, kind="ecd", version="1"):
        register_classes = cls._get_level2_registers(kind, version)
        for register_class in register_classes:
            registers = register_class.search([])  # TODO company_id filter?
            registers.unlink()

    @api.model
    def import_file(cls, filename, kind="ecd", version="1"):
        """
        ex:
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_ecd.txt", "ecd")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_efd_icms_ipi.txt", "efd_icms_ipi")
        env["l10n_br_sped.mixin"].import_file("/odoo/links/l10n_br_sped_spec/demo/demo_efd_pis_cofins_multi.txt", "efd_pis_cofins")
        """
        with open(filename) as spedfile:
            last_level = 0
            previous_register = None
            for line in [line.rstrip('\r\n') for line in spedfile]:
                reg_code = line.split('|')[1]
                version = LAYOUT_VERSIONS[kind]
                register_class = cls.env.get("l10n_br_sped.%s.%s.%s" % (kind, version, reg_code.lower(),), None)
                print("\nREF", reg_code, register_class)
                if register_class is None:
                    if "001" in reg_code or "990" in reg_code or reg_code == "9999":
                        continue
                    if reg_code in ("0000", "0007"): # FIXME
                        continue
                    raise UserError("register %s doesn't match Odoo SPED structure!" % (reg_code,))

                if register_class._sped_level < 3:  # TODO if more than +1 -> error!
                    parents = []
                    parent = None
                    last_level = register_class._sped_level
                elif register_class._sped_level > last_level:  # TODO if more than +1 -> error!
                    parents.append(previous_register)
                    parent = parents[-1]
                    last_level = register_class._sped_level
                elif register_class._sped_level < last_level:
                    parents.pop()
                    parent = parents[-1]
                    last_level = register_class._sped_level
 
                values = line.split('|')[2:][:-1]
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
                        print("BAD REGISTER FIELDS!! more values than fields in Odoo!", values, fname)
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
                            vals[fname] = float(val.replace(",","."))
                    elif field.type == "date":
                        if val != "":
                            vals[fname] = datetime.datetime.strptime(val, "%d%m%Y")
                    else:
                        vals[fname] = val
 
                if parent:
                    vals["reg_%s_ids_Registro%s_id" % (register_class._name.split(".")[-1].upper(), parent._name.split(".")[-1].upper())] = parent.id
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
        sped.write("\n|0000|")  # TODO content of 0000
        for register_class in register_level2_classes:
            bloco = register_class._name[-4:][0]
            if bloco != last_bloco:
                if last_bloco:
                    sped.write("\n|" + last_bloco + "990|42|")  # TODO count nb of bloco lines
                sped.write("\n|" + bloco + "001|0|")

            registers = register_class.search([])  # TODO filter with company_id?
            registers.generate_register_text(sped)  # TODO use yield!
            last_bloco = bloco
 
        if kind == "ecf":  # WTF why is it different?? You kidding me? or is it an error?
            sped.write("\n|" + bloco + "099|42|")  # TODO count nb of bloco lines
        else: 
            sped.write("\n|" + bloco + "990|42|")
        sped.write("\n|9999|42|")  # TODO nb of sped lines
        return sped.getvalue()

    def _get_level2_registers(cls, kind="ecd", version="1"):
        register_model_names = list(filter(lambda x: "l10n_br_sped.%s.%s" % (kind, version) in x, cls.env.keys()))
        register_level2_models = [cls.env[m] for m in register_model_names if cls.env[m]._sped_level == 2]
        return sorted(
            register_level2_models,
            key=lambda x: x._name[-4:][0] == "0"  # hacky bloco ordering that just does the job
            and "a" + x._name[-4:]
            or x._name[-4:][0] == "9"
            and "d" + x._name[-4:]
            or x._name[-4:][0] == "1"
            and "c" + x._name[-4:]
            or "b" + x._name[-4:],
        )

    def generate_register_text(self, sped):
        code = self._name[-4:].upper()
        keys =[i[0] for i in filter(
            lambda i: "company" not in i[0] and "currency" not in i[0] and not i[1].automatic and i[0] and i[1].type not in ("many2one",),
            self._fields.items()
        )]
        if not keys:  # happend with ECD I550, I555 and I555 with "LEIAUTE PARAMETRIZÁVEL"
            keys = ["id"]  # BUT should not happen!
        vals_list = self.read(keys)
        for vals in vals_list:
            sped.write("\n|%s|" % (code,))
            children = []
            for k, v in vals.items():
                if k == "id":
                    continue

                if self._fields[k].type == "one2many":
                    children.append(self.env[self._fields[k].comodel_name].search([("id", "in", v)]))
                elif self._fields[k].type != "many2one":
                    if self._fields[k].type == "date":
                        if v:
                            val = v.strftime("%d%m%Y")
                        else:
                            val = ""
                    else:
                        val = str(v)
                    sped.write(val + "|")

            for child in children:
                child.generate_register_text(sped)  # TODO use yield
        return sped


