from ..models.python_sped.sped.fci import arquivos
import base64
from openerp import api
from openerp.exceptions import Warning
from openerp.addons.l10n_br_base.tools.misc import punctuation_rm



@api.multi
def gera_fci(fci):
    arq = arquivos.ArquivoDigital()

    cpf_cnpj_numbers = punctuation_rm(fci.company_id.partner_id.cnpj_cpf)
    input0000 = ('0000|' + cpf_cnpj_numbers + '|' +
                 fci.company_id.partner_id.name + '|' + '1.0')
    input0010 = ('0010|' + fci.company_id.partner_id.cnpj_cpf + '|' +
                 fci.company_id.partner_id.legal_name + '|' +
                 fci.company_id.partner_id.street + ', ' +
                 fci.company_id.partner_id.number + '|' +
                 fci.company_id.partner_id.zip + '|' +
                 fci.company_id.partner_id.l10n_br_city_id.name + '|' +
                 fci.company_id.partner_id.state_id.code)
    for line in fci.fci_line:
        if not line.valor_parcela_importada:
            raise Warning(('Error!'), (
                'O campo Valor parcela importada nao pode ser zero'))
        else:
            input5020 = ('5020|' + line.name + '|' + str(
                line.ncm_id) + '|' + line.default_code + '|' + str(
                line.ean13) + '|' + line.product_uom.name + '|' + str(
                line.list_price) + '|' + str(
                line.valor_parcela_importada) + '|' + str(
                line.conteudo_importacao))
        arq.read_registro(input5020)
    arq.read_registro(input0000)
    arq.read_registro(input0010)

    return base64.b64encode(arq.getstring().encode('utf8'))


def importa_fci(file_name):
    arq_entrada = arquivos.ArquivoDigital()

    file_entrada = base64.decodestring(file_name)
    file_entrada = file_entrada.lstrip()
    file_entrada = file_entrada.rstrip()
    registros = file_entrada.split('\r\n')

    for reg in registros:
        arq_entrada.read_registro(reg)

    list_default_code = []
    list_fci_codes = []
    a= arq_entrada._registro_abertura.valores[02]
    a = a[:2] + "." + a[2:5] + "." + a[5:8] + "/" + a[8:12] + "-" + a[-2:]


    res = {
        'hash_code': arq_entrada._registro_abertura.valores[05],
        'dt_recepcao': arq_entrada._registro_abertura.valores[6],
        'cod_recepcao': arq_entrada._registro_abertura.valores[7],
        'dt_validacao': arq_entrada._registro_abertura.valores[8],
        'in_validacao': arq_entrada._registro_abertura.valores[9],
        'cnpj_cpf': a,
        'default_code': list_default_code,
        'fci_codes': list_fci_codes
    }


    # a = res['cnpj_cpf'][:2] + "." + res['cnpj_cpf'][2:5] + "." + res['cnpj_cpf'][5:8] + "/" + res['cnpj_cpf'][8:12] + "-" + res['cnpj_cpf'][-2:]
    # res['cnpj_cpf'] = a
    # print a

    for registro5020 in arq_entrada._blocos['5'].registros:
        if registro5020.valores[01] == '5020':
            list_default_code.append(registro5020.valores[05])
            list_fci_codes.append(registro5020.valores[10])
    res['default_code'] = list_default_code

    return res
