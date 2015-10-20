from ..models.python_sped.sped.fci import arquivos
import base64


def gera_fci(fci):
    arq = arquivos.ArquivoDigital()

    input0000 = ('0000|' + fci.company_id.partner_id.cnpj_cpf + '|' +
        fci.company_id.partner_id.name + '|' + '1.0')
    input0010 = ('0010|' + fci.company_id.partner_id.cnpj_cpf + '|' +
        fci.company_id.partner_id.legal_name + '|' +
        fci.company_id.partner_id.street + ', ' +
        fci.company_id.partner_id.number + '|' +
        fci.company_id.partner_id.zip + '|' +
        fci.company_id.partner_id.l10n_br_city_id.name + '|' +
        fci.company_id.partner_id.state_id.code)
    for line in fci.fci_line:
        input5020 = ('5020|' + line.name + '|' + str(
            line.ncm_id) + '|' + line.default_code + '|' + str(
            line.ean13) + '|' + line.product_uom.name + '|' + str(
            line.list_price) + '|' + str(
            line.valor_parcela_importada) + '|' + str(
            line.conteudo_importacao))
        arq.read_registro(input5020)
    arq.read_registro(input0000)
    arq.read_registro(input0010)
    arqSaida = open('saida.txt', 'w')
    arqSaida.write(arq.getstring().encode('utf8'))
    arqSaida.close()
    return

def importa_fci(file_name):
    arq_entrada = arquivos.ArquivoDigital()

    file_entrada = base64.decodestring(file_name)
    file_entrada = file_entrada.lstrip()
    file_entrada = file_entrada.rstrip()
    registros = file_entrada.split('\r\n')

    print file_entrada

    for reg in registros:
        arq_entrada.read_registro(reg)

    list_default_code = []
    list_fci_codes = []
    res = {
        'hash_code': arq_entrada._registro_abertura.valores[05],
        'dt_recepcao': arq_entrada._registro_abertura.valores[6],
        'cod_recepcao': arq_entrada._registro_abertura.valores[7],
        'dt_validacao': arq_entrada._registro_abertura.valores[8],
        'in_validacao': arq_entrada._registro_abertura.valores[9],
        'cnpj_cpf': arq_entrada._registro_abertura.valores[02],
        'default_code': list_default_code,
        'fci_codes': list_fci_codes
    }

    for registro5020 in arq_entrada._blocos['5'].registros:
        if registro5020.valores[01] == '5020':
            list_default_code.append(registro5020.valores[05])
            list_fci_codes.append(registro5020.valores[10])

    res['default_code'] = list_default_code

    return res
