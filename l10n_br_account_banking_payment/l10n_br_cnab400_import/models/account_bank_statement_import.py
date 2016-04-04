# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Fernando Marcato Rodrigues
#    Copyright (C) 2015 KMEE - www.kmee.com.br
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import tempfile
import StringIO
from openerp import api, models, fields
from openerp.tools.translate import _
from openerp.exceptions import Warning

try:
    import cnab240
    from cnab240.tipos import ArquivoCobranca400 as cnab_parser
    from cnab240.bancos import bradesco_cobranca_retorno_400 as bradesco
    from cnab240.ocorrencias import retorna_ocorrencia, retorna_motivios_ocorrencia
    import codecs
except:
    raise Exception(_('Please install python lib PyCNAB'))


_logger = logging.getLogger(__name__)


MODOS_IMPORTACAO_CNAB = [
    ('bradesco_cobranca_400', u'Bradesco Cobrança 400'),
]

CODIGO_MOTIVOS_OCORRENCIA = {
    '02': {
        'codigo_ocorrencia': '02',
        'texto': 'Entrada confirmada',
        '00': 'Ocorrência aceita',
        '01': 'Código do Banco inválido',
        '04': 'Código do movimento não permitido para a carteira (NOVO)',
        '15': 'Características da cobrança incompatíveis (NOVO)',
        '17': 'Data de vencimento anterior a data de emissão',
        '21': 'Espécie do Título inválido',
        '24': 'Data da emissão inválida',
        '27': 'Valor/taxa de juros mora inválido (NOVO)',
        '38': 'Prazo para protesto/ Negativação inválido (ALTERADO)',
        '39': 'Pedido para protesto/ Negativação não permitido para o título (ALTERADO)',
        '43': 'Prazo para baixa e devolução inválido',
        '45': 'Nome do Pagador inválido',
        '46': 'Tipo/num. de inscrição do Pagador inválidos',
        '47': 'Endereço do Pagador não informado',
        '48': 'CEP Inválido',
        '50': 'CEP referente a Banco correspondente',
        '53': 'No de inscrição do Pagador/avalista inválidos (CPF/CNPJ)',
        '54': 'Pagadorr/avalista não informado',
        '67': 'Débito automático agendado',
        '68': 'Débito não agendado - erro nos dados de remessa',
        '69': 'Débito não agendado - Pagador não consta no cadastro de autorizante',
        '70': 'Débito não agendado - Beneficiário não autorizado pelo Pagador',
        '71': 'Débito não agendado - Beneficiário não participa da modalidade de déb.automático',
        '72': 'Débito não agendado - Código de moeda diferente de R$',
        '73': 'Débito não agendado - Data de vencimento inválida/vencida',
        '75': 'Débito não agendado - Tipo do número de inscrição do pagador debitado inválido',
        '76': 'Pagador Eletrônico DDA (NOVO)- Esse motivo somente será disponibilizado no arquivo retorno para as empresas cadastradas nessa condição.',
        '86': 'Seu número do documento inválido',
        '89': 'Email Pagador não enviado – título com débito automático (NOVO)',
        '90': 'Email pagador não enviado – título de cobrança sem registro (NOVO)',
    },
    '03': {
        'codigo_ocorrencia': '03',
        'texto': 'entrada rejeitada',
        '00': 'N/A',
        '02': 'Código do registro detalhe inválido',
        '03': 'Código da ocorrência inválida',
        '04': 'Código de ocorrência não permitida para a carteira',
        '05': 'Código de ocorrência não numérico',
        '07': 'Agência/conta/Digito - |Inválido',
        '08': 'Nosso número inválido',
        '09': 'Nosso número duplicado',
        '10': 'Carteira inválida',
        '13': 'Identificação da emissão do bloqueto inválida (NOVO)',
        '16': 'Data de vencimento inválida',
        '18': 'Vencimento fora do prazo de operação',
        '20': 'Valor do Título inválido',
        '21': 'Espécie do Título inválida',
        '22': 'Espécie não permitida para a carteira',
        '24': 'Data de emissão inválida',
        '28': 'Código do desconto inválido (NOVO)',
        '38': 'Prazo para protesto/ Negativação inválido (ALTERADO)',
        '44': 'Agência Beneficiário não prevista',
        '45': 'Nome do pagador não informado (NOVO)',
        '46': 'Tipo/número de inscrição do pagador inválidos (NOVO)',
        '47': 'Endereço do pagador não informado (NOVO)',
        '48': 'CEP Inválido (NOVO)',
        '50': 'CEP irregular - Banco Correspondente',
        '63': 'Entrada para Título já cadastrado',
        '65': 'Limite excedido (NOVO)',
        '66': 'Número autorização inexistente (NOVO)',
        '68': 'Débito não agendado - erro nos dados de remessa',
        '69': 'Débito não agendado - Pagador não consta no cadastro de autorizante',
        '70': 'Débito não agendado - Beneficiário não autorizado pelo Pagador',
        '71': 'Débito não agendado - Beneficiário não participa do débito Automático',
        '72': 'Débito não agendado - Código de moeda diferente de R$',
        '73': 'Débito não agendado - Data de vencimento inválida',
        '74': 'Débito não agendado - Conforme seu pedido, Título não registrado',
        '75': 'Débito não agendado – Tipo de número de inscrição do debitado inválido',
    },

    '06': {
        'codigo_ocorrencia': '06',
        'texto': 'Liquidação normal',
        '00': 'Título pago com dinheiro',
        '15': 'Título pago com cheque',
        '42': 'Rateio não efetuado, cód. Calculo 2 (VLR. Registro) e v (NOVO)'
    },

    '10': {
        'codigo_ocorrencia': '10',
        'texto': 'Baixado conforme instruções da Agência',
        '00': 'Baixado Conforme Instruções da Agência',
        '14': 'Título Protestado',
        '15': 'Título excluído',
        '16': 'Título Baixado pelo Banco por decurso Prazo',
        '17': 'Titulo Baixado Transferido Carteira',
        '20': 'Titulo Baixado e Transferido para Desconto',
    },

    '19': {
        'codigo_ocorrencia': '19',
        'texto': 'Confirmação Receb. Inst. de Protesto',
        '00': 'N/A',
    },

    '23': {
        'codigo_ocorrencia': '23',
        'texto': 'Entrada do Título em Cartório',
        '00': 'N/A',
    },

    '28': {
        'codigo_ocorrencia': '28',
        'texto': 'Débito de tarifas/custas',
        '00': 'N/A',
        '02': 'Tarifa de permanência título cadastrado (NOVO)',
        '03': 'Tarifa de sustação/Excl Negativação (ALTERADO)',
        '04': 'Tarifa de protesto/Incl Negativação (ALTERADO)',
        '05': 'Tarifa de outras instruções (NOVO)',
        '06': 'Tarifa de outras ocorrências (NOVO)',
        '08': 'Custas de protesto',
        '12': 'Tarifa de registro (NOVO)',
        '13': 'Tarifa título pago no Bradesco (NOVO)',
        '14': 'Tarifa título pago compensação (NOVO)',
        '15': 'Tarifa título baixado não pago (NOVO)',
        '16': 'Tarifa alteração de vencimento (NOVO)',
        '17': 'Tarifa concessão abatimento (NOVO)',
        '18': 'Tarifa cancelamento de abatimento (NOVO)',
        '19': 'Tarifa concessão desconto (NOVO)',
        '20': 'Tarifa cancelamento desconto (NOVO)',
        '21': 'Tarifa título pago cics (NOVO)',
        '22': 'Tarifa título pago Internet (NOVO)',
        '23': 'Tarifa título pago term. gerencial serviços (NOVO)',
        '24': 'Tarifa título pago Pág-Contas (NOVO)',
        '25': 'Tarifa título pago Fone Fácil (NOVO)',
        '26': 'Tarifa título Déb. Postagem (NOVO)',
        '27': 'Tarifa impressão de títulos pendentes (NOVO)',
        '28': 'Tarifa título pago BDN (NOVO)',
        '29': 'Tarifa título pago Term. Multi Função (NOVO)',
        '30': 'Impressão de títulos baixados (NOVO)',
        '31': 'Impressão de títulos pagos (NOVO)',
        '32': 'Tarifa título pago Pagfor (NOVO)',
        '33': 'Tarifa reg/pgto – guichê caixa (NOVO)',
        '34': 'Tarifa título pago retaguarda (NOVO)',
        '35': 'Tarifa título pago Subcentro (NOVO)',
        '36': 'Tarifa título pago Cartão de Crédito (NOVO)',
        '37': 'Tarifa título pago Comp Eletrônica (NOVO)',
        '38': 'Tarifa título Baix. Pg. Cartório (NOVO)',
        '39': 'Tarifa título baixado acerto BCO (NOVO)',
        '40': 'Baixa registro em duplicidade (NOVO)',
        '41': 'Tarifa título baixado decurso prazo (NOVO)',
        '42': 'Tarifa título baixado Judicialmente (NOVO)',
        '43': 'Tarifa título baixado via remessa (NOVO)',
        '44': 'Tarifa título baixado rastreamento (NOVO)',
        '45': 'Tarifa título baixado conf. Pedido (NOVO)',
        '46': 'Tarifa título baixado protestado (NOVO)',
        '47': 'Tarifa título baixado p/ devolução (NOVO)',
        '48': 'Tarifa título baixado franco pagto (NOVO)',
        '49': 'Tarifa título baixado SUST/RET/CARTÓRIO (NOVO)',
        '50': 'Tarifa título baixado SUS/SEM/REM/CARTÓRIO (NOVO)',
        '51': 'Tarifa título transferido desconto (NOVO)',
        '52': 'Cobrado baixa manual (NOVO)',
        '53': 'Baixa por acerto cliente (NOVO)',
        '54': 'Tarifa baixa por contabilidade (NOVO)',
        '55': 'Tr. tentativa cons deb aut',
        '56': 'Tr. credito online',
        '57': 'Tarifa reg/pagto Bradesco Expresso',
        '58': 'Tarifa emissão Papeleta (NOVO)',
        '59': 'Tarifa fornec papeleta semi preenchida (NOVO)',
        '60': 'Acondicionador de papeletas (RPB)S (NOVO)',
        '61': 'Acond. De papelatas (RPB)s PERSONAL (NOVO)',
        '62': 'Papeleta formulário branco (NOVO)',
        '63': 'Formulário A4 serrilhado (NOVO)',
        '64': 'Fornecimento de softwares transmiss (NOVO)',
        '65': 'Fornecimento de softwares consulta (NOVO)',
        '66': 'Fornecimento Micro Completo (NOVO)',
        '67': 'Fornecimento MODEN (NOVO)',
        '68': 'Fornecimento de máquina FAX (NOVO)',
        '69': 'Fornecimento de máquinas óticas (NOVO)',
        '70': 'Fornecimento de Impressoras (NOVO)',
        '71': 'Reativação de título (NOVO)',
        '72': 'Alteração de produto negociado (NOVO)',
        '73': 'Tarifa emissão de contra recibo (NOVO)',
        '74': 'Tarifa emissão 2a via papeleta (NOVO)',
        '75': 'Tarifa regravação arquivo retorno (NOVO)',
        '76': 'Arq. Títulos a vencer mensal (NOVO)',
        '77': 'Listagem auxiliar de crédito (NOVO)',
        '78': 'Tarifa cadastro cartela instrução permanente (NOVO)',
        '79': 'Canalização de Crédito (NOVO)',
        '80': 'Cadastro de Mensagem Fixa (NOVO)',
        '81': 'Tarifa reapresentação automática título (NOVO)',
        '82': 'Tarifa registro título déb. Automático (NOVO)',
        '83': 'Tarifa Rateio de Crédito (NOVO)',
        '84': 'Emissão papeleta sem valor (NOVO)',
        '85': 'Sem uso (NOVO)',
        '86': 'Cadastro de reembolso de diferença (NOVO)',
        '87': 'Relatório fluxo de pagto (NOVO)',
        '88': 'Emissão Extrato mov. Carteira (NOVO)',
        '89': 'Mensagem campo local de pagto (NOVO)',
        '90': 'Cadastro Concessionária serv. Publ. (NOVO)',
        '91': 'Classif. Extrato Conta Corrente (NOVO)',
        '92': 'Contabilidade especial (NOVO)',
        '93': 'Realimentação pagto (NOVO)',
        '94': 'Repasse de Créditos (NOVO)',
        '96': 'Tarifa reg. Pagto outras mídias (NOVO)',
        '97': 'Tarifa Reg/Pagto – Net Empresa (NOVO)',
        '98': 'Tarifa título pago vencido (NOVO)',
        '99': 'TR Tít. Baixado por decurso prazo (NOVO)',
        # '100': 'Arquivo Retorno Antecipado (NOVO)',
        # '101': 'Arq retorno Hora/Hora (NOVO)',
        # '102': 'TR. Agendamento Déb Aut (NOVO)',
        # '105': 'TR. Agendamento rat. Crédito (NOVO)',
        # '106': 'TR Emissão aviso rateio (NOVO)',
        # '107': 'Extrato de protesto (NOVO)',
    },

    '32': {
        'codigo_ocorrencia': '32',
        'texto': 'Instrução Rejeitada',
        '00': 'N/A',
        '01': 'Código do Banco inválido',
        '02': 'Código do registro detalhe inválido',
        '04': 'Código de ocorrência não permitido para a carteira',
        '05': 'Código de ocorrência não numérico',
        '07': 'Agência/Conta/dígito inválidos',
        '08': 'Nosso número inválido',
        '10': 'Carteira inválida',
        '15': 'Características da cobrança incompatíveis',
        '16': 'Data de vencimento inválida',
        '17': 'Data de vencimento anterior a data de emissão',
        '18': 'Vencimento fora do prazo de operação',
        '20': 'Valor do título inválido',
        '21': 'Espécie do Título inválida',
        '22': 'Espécie não permitida para a carteira',
        '24': 'Data de emissão inválida',
        '28': 'Código de desconto via Telebradesco inválido',
        '29': 'Valor do desconto maior/igual ao valor do Título',
        '30': 'Desconto a conceder não confere',
        '31': 'Concessão de desconto - Já existe desconto anterior',
        '33': 'Valor do abatimento inválido',
        '34': 'Valor do abatimento maior/igual ao valor do Título',
        '36': 'Concessão abatimento - Já existe abatimento anterior',
        '38': 'Prazo para protesto/ Negativação inválido (ALTERADO)',
        '39': 'Pedido para protesto/ Negativação não permitido para o título (ALTERADO)',
        '40': 'Título com ordem/pedido de protesto/Negativação emitido (ALTERADO)',
        '41': 'Pedido de sustação/excl p/ Título sem instrução de protesto/Negativação (ALTERADO)',
        '42': 'Código para baixa/devolução inválido',
        '45': 'Nome do Pagador não informado',
        '46': 'Tipo/número de inscrição do Pagador inválidos',
        '47': 'Endereço do Pagador não informado',
        '48': 'CEP Inválido',
        '50': 'CEP referente a um Banco correspondente',
        '53': 'Tipo de inscrição do pagador avalista inválidos',
        '60': 'Movimento para Título não cadastrado',
        '85': 'Título com pagamento vinculado',
        '86': 'Seu número inválido',
        '94': 'Título Penhorado – Instrução Não Liberada pela Agência (NOVO)',
        '97': ' Instrução não permitida título negativado (NOVO)',
        '98': ' Inclusão Bloqueada face a determinação Judicial (NOVO)',
        '99': ' Telefone beneficiário não informado / inconsistente (NOVO)',
    },

    '33': {
        'codigo_ocorrencia': '33',
        'texto': 'Confirmação Pedido Alteração Outros Dados',
        '00': 'N/A',

    },
}

class AccountBankStatementImport(models.TransientModel):
    """  """
    _inherit = 'account.bank.statement.import'

    @api.model
    def _check_cnab(self, data_file):
        if cnab_parser is None:
            return False
        try:
            cnab400_file = tempfile.NamedTemporaryFile()
            cnab400_file.seek(0)
            cnab400_file.write(data_file)
            cnab400_file.flush()
            ret_file = codecs.open(cnab400_file.name, encoding='ascii')
            cnab = cnab_parser(bradesco, arquivo=ret_file)
        except:
            return False

        if len(cnab.lotes) == 0:
            cnab240_file = tempfile.NamedTemporaryFile()
            cnab240_file.seek(0)
            cnab240_file.write(data_file)
            cnab240_file.flush()
            ret_file = codecs.open(cnab240_file.name, encoding='ascii')
            cnab2 = cnab240.tipos.Arquivo(
                cnab240.bancos.bradesco, arquivo=ret_file
            )
            return cnab2
        return cnab

    # @api.model
    # def _find_bank_account_id(self, account_number):
    #     """ Get res.partner.bank ID """
    #     bank_account_id = None
    #     if account_number:
    #         bank_account_ids = self.env['res.partner.bank'].search(
    #             [('acc_number', '=', str(account_number))], limit=1)
    #         if bank_account_ids:
    #             bank_account_id = bank_account_ids[0].id
    #     return bank_account_id

    # @api.model
    # def _complete_statement(self, stmt_vals, journal_id, account_number):
    #     """Complete statement from information passed.
    #         unique_import_id can be imported more than 1 time."""
    #     stmt_vals['journal_id'] = journal_id
    #
    #     #TODO pesquisar cnpj do parceiro para a reconciliação
    #     for line_vals in stmt_vals['transactions_cnab_return']:
    #         # write on move_line
    #         self.write_data_on_move_line(line_vals)
    #         pass
    #
    #     for line_vals in stmt_vals['transactions']:
    #         self.write_data_on_paid_move_line(line_vals)
    #         unique_import_id = line_vals.get('unique_import_id', False)
    #         if unique_import_id:
    #             line_vals['unique_import_id'] = unique_import_id
    #         if not line_vals.get('bank_account_id'):
    #             # Find the partner and his bank account or create the bank
    #             # account. The partner selected during the reconciliation
    #             # process will be linked to the bank when the statement is
    #             # closed.
    #             partner_id = False
    #             bank_account_id = False
    #             partner_account_number = line_vals.get('account_number')
    #             if partner_account_number:
    #                 bank_model = self.env['res.partner.bank']
    #                 banks = bank_model.search(
    #                     [('acc_number', '=', partner_account_number)], limit=1)
    #                 if banks:
    #                     bank_account_id = banks[0].id
    #                     partner_id = banks[0].partner_id.id
    #                 else:
    #                     bank_obj = self._create_bank_account(
    #                         partner_account_number)
    #                     bank_account_id = bank_obj and bank_obj.id or False
    #             line_vals['partner_id'] = partner_id
    #             line_vals['bank_account_id'] = bank_account_id
    #     return stmt_vals

    @api.multi
    def _parse_file(self, data_file):
        """Parse a CNAB file."""
        cnab = self._check_cnab(data_file)
        try:
            if cnab.header.literal_servico == 'COBRANCA':
                event_list = []

                try:
                    for lote in cnab.lotes:

                        data_criacao = str(cnab.header.arquivo_data_de_geracao)
                        if len(data_criacao) < 6:
                            data_criacao = '0' + data_criacao
                        dia_criacao = data_criacao[:2]
                        mes_criacao = data_criacao[2:4]
                        ano_criacao = data_criacao[4:6]
                        name = cnab.header.literal_retorno + " " + cnab.header.literal_servico + " " + cnab.header.nome_banco + " - " + dia_criacao + "/" + mes_criacao + "/" + ano_criacao
                        vals_bank_statement = {
                            'name': name,
                            'transactions': {},
                            'balance_end_real': float(cnab.trailer
                                .valor_registros_ocorrencia_02_confirmacao)/100,
                            'date': dia_criacao + "-" + mes_criacao + "-" + ano_criacao,
                        }

                        for evento in lote.eventos:
                            is_created = self.create_cnab_move(evento, cnab.header.nome_banco)
                            if is_created:
                                if evento.identificacao_ocorrencia == 6:
                                    data = str(evento.data_ocorrencia_banco)
                                    if len(data) < 6:
                                        data = '0' + data
                                    dia = data[:2]
                                    mes = data[2:4]
                                    ano = data[4:6]
                                    partner_id = False
                                    cnpj_cpf = str(evento.numero_documento)[-14:]
                                    # invoice_number = 'SAJ/2016/005'
                                    # invoices = self.env['account.invoice']
                                    # invoice = invoices.search([
                                    #     ('number', '=', invoice_number)
                                    # ])
                                    # partner = invoice.partner_id
                                    bank_account = self.env['res.partner.bank'].\
                                        search([
                                            (
                                                'acc_number', '=', evento.identificacao_empresa_cedente_banco[11:16]
                                            )
                                        ])
                                    vals_line = {
                                        'date': dia + "-" + mes + "-" + ano,
                                        'name': evento.identificacao_titulo_banco,
                                        'ref': evento.numero_documento,
                                        'amount': float(evento.valor_titulo)/100,
                                        'unique_import_id':
                                            evento.identificacao_titulo_banco,
                                        # 'partner_id': partner and partner.id or
                                        #               False,
                                        # 'partner_name': (
                                        #     partner and partner.legal_name or False
                                        # ),
                                        'bank_account_id': bank_account.id,
                                    }
                                    event_list.append(vals_line)
                        vals_bank_statement['transactions'] = event_list
                except Exception, e:
                    raise UserError(_(
                        "Erro!\n "
                        "Mensagem:\n\n %s" % e.message
                    ))

                return False, str(
                           cnab.lotes[0].eventos[0]
                               .identificacao_empresa_cedente_banco[11:16]
                       ), [vals_bank_statement]
        except:
            return super(AccountBankStatementImport, self)._parse_file(
                data_file)

    @api.model
    def create_cnab_move(self, evento, nome_banco):
        data = str(evento.data_ocorrencia_banco)
        if len(data) < 6:
            data = '0' + data
        dia = data[:2]
        mes = data[2:4]
        ano = data[4:6]

        identificacao_ocorrencia = evento.identificacao_ocorrencia
        id_motivos = evento.motivo_rejeicao_ocorrencia_109_110

        motivos = retorna_motivios_ocorrencia(identificacao_ocorrencia, id_motivos)

        move_line_name = evento.numero_documento[:-2]
        move_line_model = self.env['account.move.line']
        move_line_item = move_line_model.search(
            [('name', '=', move_line_name)], limit=1)

        if move_line_item:
            move_line_item.transaction_ref = evento.numero_documento[:-2]
            move_line_item.ml_identificacao_titulo_no_banco = evento.identificacao_titulo_banco

        vals = {
            'move_line_id': move_line_item and move_line_item.id or False,
            'bank_title_name': evento.identificacao_titulo_banco,
            'title_name_at_company': evento.numero_documento[:-2],
            #'nosso_numero': evento.identificacao_titulo_banco,
            'sequencia_no_titulo': evento.numero_documento[-1:],
            'data_ocorrencia': dia + '/' + mes + '/' + ano,
            'str_ocorrencia': retorna_ocorrencia(identificacao_ocorrencia),
            'cod_ocorrencia': evento.identificacao_ocorrencia,
            'str_motiv_a': motivos[0],
            'str_motiv_b': motivos[1],
            'str_motiv_c': motivos[2],
            'str_motiv_d': motivos[3],
            'str_motiv_e': motivos[4],
            'valor': float(evento.valor_titulo)/100,
        }
        cnab_move = self.env['l10n_br_cnab.move']

        return cnab_move.create(vals)
