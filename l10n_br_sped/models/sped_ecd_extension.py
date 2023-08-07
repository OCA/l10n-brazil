from odoo import api, models, fields


class RegistroI550(models.Model):
    """
    Detalhes do Livro Razão Auxiliar com Leiaute Parametrizável
    """

    _inherit = "l10n_br_sped.ecd.9.i550"

    RZ_CONT = fields.Char()  # according to pdf specification

    @api.model
    def import_register(cls, line):
        vals = {"RZ_CONT": "|".join(line.split("|")[2:][:-1])}
        return vals

    def generate_register_text(self, sped, line_count={}):
        code = self._name[-4:].upper()
        vals_list = self.read(["RZ_CONT", "reg_I555_ids"])
        for vals in vals_list:
            sped.write("\n|%s|" % (code,))
            sped.write(vals["RZ_CONT"])
            sped.write("|")
            line_count[0] += 1
            children = self.env["l10n_br_sped.ecd.9.i555"].search([("id", "in", vals["reg_I555_ids"])])
            for child in children:
                child.generate_register_text(sped, line_count)  # NOTE use yield?
        return sped 

class RegistroI555(models.Model):
    """
    Totais no Livro Razão Auxiliar com Leiaute Parametrizável
    """

    _inherit = "l10n_br_sped.ecd.9.i555"

    RZ_CONT_TOT = fields.Char()  # according to pdf specification

    @api.model
    def import_register(cls, line):
        vals = {"RZ_CONT_TOT": "|".join(line.split("|")[2:][:-1])}
        return vals

    def generate_register_text(self, sped, line_count={}):
        code = self._name[-4:].upper()
        keys = [i[0] for i in self._fields.items()]
        vals_list = self.read(keys)
        for vals in vals_list:
            sped.write("\n|%s|" % (code,))
            sped.write(vals.get("RZ_CONT_TOT", ""))
            sped.write("|")
            line_count[0] += 1
