from ..models.python_sped.sped.fci import arquivos
import base64


def gera_fci(company, fci):
    arq = arquivos.ArquivoDigital()

    input0000 = '0000|' + company.cnpj_cpf + '|' + company.name + '|' + '1.0'
    input0010 = ('0010|' + company.cnpj_cpf + '|' + company.legal_name + '|' + company.street + ', ' + company.number + '|' + company.zip + '|' + company.state_id.name + '|' + company.state_id.code)

    for line in fci:
        input5020 = ('5020|' + line.name + '|' + str(line.ncm_id.name) + '|' + line.default_code + '|' + str(line.ean13) + '|' + line.uom_id.name + '|' + str(line.lst_price) + '|' + '2056' + '|' + '45')
        print input5020

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
    registros= file_entrada.split('\r\n')

    for reg in registros:
        arq_entrada.read_registro(reg)

    list_default_code = []
    list_fci_codes = []
    res = {
        'hash_code': arq_entrada._registro_abertura.valores[05],
        'dt_recepcao':arq_entrada._registro_abertura.valores[6],
        'cod_recepcao':arq_entrada._registro_abertura.valores[7],
        'dt_validacao': arq_entrada._registro_abertura.valores[8],
        'in_validacao': arq_entrada._registro_abertura.valores[9],
        'cnpj_cpf': arq_entrada._registro_abertura.valores[02],
        'default_code':list_default_code,
        'fci_codes': list_fci_codes
    }


    for registro5020 in arq_entrada._blocos['5'].registros:
         if registro5020.valores[01] == '5020':
            list_default_code.append(registro5020.valores[05])
            list_fci_codes.append(registro5020.valores[10])

    res['default_code'] = list_default_code

    return res

