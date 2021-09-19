import wdb

import logging
import time
from threading import Thread, Lock
from requests import ConnectionError
from decimal import Decimal as D
import io
from odoo.addons.hw_proxy.controllers import main as hw_proxy
from odoo import http
import base64
import string

_logger = logging.getLogger(__name__)

try:
    import satcfe
    from satcomum import constantes
    from satcfe import ClienteSATLocal
    from satcfe import ClienteSATHub
    from satcfe import BibliotecaSAT
    from satcfe.entidades import Emitente
    from satcfe.entidades import Destinatario
    from satcfe.entidades import LocalEntrega
    from satcfe.entidades import Detalhamento
    from satcfe.entidades import ProdutoServico
    from satcfe.entidades import Imposto
    from satcfe.entidades import MeioPagamento
    from satcfe.entidades import CFeVenda
    from satcfe.entidades import DescAcrEntr
    from satcfe.entidades import CFeCancelamento
    from satcfe.entidades import (
        COFINSAliq,
        COFINSNT,
        COFINSOutr,
        COFINSQtde,
        COFINSSN,
        COFINSST,
        ICMS00,
        ICMS40,
        ICMSSN102,
        ICMSSN900,
        ISSQN,
        PISAliq,
        PISNT,
        PISOutr,
        PISQtde,
        PISSN,
        PISST,
    )
    from satcfe.excecoes import ErroRespostaSATInvalida
    from satcfe.excecoes import ExcecaoRespostaSAT
    from satextrato import ExtratoCFeVenda
    from satextrato import ExtratoCFeCancelamento
    from erpbrasil.base.misc import punctuation_rm
    from satextrato.config import carregar, padrao
except ImportError:
    _logger.error('Odoo module hw_l10n_br_pos depends on the satcfe module')
    satcfe = None

TAX_FRAMEWORK_SIMPLES = "1"
TAX_FRAMEWORK_SIMPLES_EX = "2"
TAX_FRAMEWORK_NORMAL = "3"

TWOPLACES = D(10) ** -2
FOURPLACES = D(10) ** -4


class Sat(Thread):
    def __init__(self, codigo_ativacao, sat_path, impressora, printer_params, fiscal_printer_type, assinatura):
        Thread.__init__(self)
        self.codigo_ativacao = codigo_ativacao
        self.sat_path = sat_path
        self.impressora = impressora
        self.printer_params = printer_params
        self.fiscal_printer_type = fiscal_printer_type
        self.lock = Lock()
        self.satlock = Lock()
        self.status = {'status': 'connecting', 'messages': []}
        self.printer = self._init_printer()
        self.device = self._get_device()
        self.assinatura = assinatura

    def lockedstart(self):
        with self.lock:
            if not self.isAlive():
                self.daemon = True
                self.start()

    def get_status(self):
        self.lockedstart()
        return self.status

    def set_status(self, status, message=None):
        if status == self.status['status']:
            if message is not None and message != self.status['messages'][-1]:
                self.status['messages'].append(message)

                if status == 'error' and message:
                    _logger.error('SAT Error: ' + message)
                elif status == 'disconnected' and message:
                    _logger.warning('Disconnected SAT: ' + message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

            if status == 'error' and message:
                _logger.error('SAT Error: ' + message)
            elif status == 'disconnected' and message:
                _logger.warning('Disconnected SAT: ' + message)

    def _get_device(self):
        if not self.sat_path and not self.codigo_ativacao:
            self.set_status('error', 'Dados do sat incorretos')
            return None
        return ClienteSATLocal(
            BibliotecaSAT(self.sat_path),
            codigo_ativacao=self.codigo_ativacao
        )

    def status_sat(self):
        with self.satlock:
            if self.device:
                try:
                    if self.device.consultar_sat():
                        self.set_status('connected', 'Connected to SAT')
                except ErroRespostaSATInvalida as ex_sat_invalida:
                    # o equipamento retornou uma resposta que não faz sentido;
                    # loga, e lança novamente ou lida de alguma maneira
                    self.device = None
                except ExcecaoRespostaSAT as ex_resposta:
                    self.set_status('disconnected', 'SAT Not Found')
                    self.device = None
                except ConnectionError as ex_conn_error:
                    self.device = None
                except Exception as ex:
                    self.set_status('error', str(ex))
                    self.device = None

    def __prepare_send_detail_cfe(self, item):
        kwargs = {}
        if item['discount']:
            kwargs['vDesc'] = D(
                (item['quantity'] * item['price']) - item['price_display']
            ).quantize(TWOPLACES)
        # estimated_taxes = D(0.01 * item['price_display']).quantize(TWOPLACES)
        estimated_taxes = D(item['amount_estimate_tax'] * item['price_without_tax']).quantize(TWOPLACES)

        produto = ProdutoServico(
            cProd=str(item['product_default_code']),
            # cEAN=str(item['product_ean']),
            xProd=item['product_name'],
            uCom=item['unit_code'],
            CFOP=str(item['cfop']),
            qCom=D(item['quantity']).quantize(FOURPLACES),
            vUnCom=D(item['price']).quantize(TWOPLACES),
            indRegra='A',
            NCM=punctuation_rm(item['ncm']),
            **kwargs
        )
        produto.validar()

        # wdb.set_trace()

        icms = pis = cofins = None

        if item['company_tax_framework'] == TAX_FRAMEWORK_SIMPLES:
            if item['icms_cst_code'] in ['101']:
                raise ErroRespostaSATInvalida
            elif item['icms_cst_code'] in ['102', '300', '500']:
                icms = ICMSSN102(
                    Orig=item['icms_origin'],
                    CSOSN=item['icms_cst_code'],
                )
            else:
                icms = ICMSSN900(
                    Orig=item['icms_origin'],
                    CSOSN=item['icms_cst_code'],
                    pICMS=D(item['icmssn_percent']).quantize(D('0.01')),
                )

            pis = PISSN(CST=item['pis_cst_code'])
            cofins = COFINSSN(CST=item['cofins_cst_code'])
        else:
            if item['icms_cst_code'] in ['00', '20', '90']:
                icms = ICMS00(
                    Orig=item['icms_origin'],
                    CST=item['icms_cst_code'],
                    pICMS=D(item['icms_percent']).quantize(D('0.01')),
                )
            elif item['icms_cst_code'] in ['40', '41', '50', '60']:
                icms = ICMS40(
                    Orig=item['icms_origin'],
                    CST=item['icms_cst_code']
                )
            #
            # PIS
            # TODO: Implementar pis ST

            al_pis_proprio = D(item['pis_percent'] / 100).quantize(D('0.0001'))

            if item['pis_cst_code'] in ['01', '02', '05']:
                pis = PISAliq(
                    CST=item['pis_cst_code'],
                    vBC=D(item['pis_base'] * item['price_without_tax']).quantize(D('0.01')),
                    # TODO: Verificar se é possível implementar no frontend
                    pPIS=al_pis_proprio,
                )
            elif item['pis_cst_code'] in ['04', '06', '07', '08', '09']:
                pis = PISNT(
                    CST=item['pis_cst_code']
                )
            elif item['pis_cst_code'] == '03':
                raise NotImplementedError
                # vr_pis_proprio
                pis = PISQtde(
                    CST=item['pis_cst_code'],
                    qBCProd=D(item['quantidade']).quantize(D('0.01')),
                    vAliqProd=D(item['vr_pis_proprio']).quantize(D('0.01'))
                )
            elif item['pis_cst_code'] == '99':
                pis = PISOutr(
                    CST=item['pis_cst_code'],
                    vBC=D(item['pis_base'] * item['price_without_tax']).quantize(D('0.01')),
                    pPIS=al_pis_proprio,
                )

            # COFINS
            # TODO: Implementer cofins ST

            al_cofins_proprio = D(item['cofins_percent'] / 100).quantize(D('0.0001'))

            if item['cofins_cst_code'] in ['01', '02', '05']:
                cofins = COFINSAliq(
                    CST=item['cofins_cst_code'],
                    vBC=D(item['cofins_base'] * item['price_without_tax']).quantize(D('0.01')),
                    pCOFINS=al_cofins_proprio,
                )
            elif item['cofins_cst_code'] in ['04', '06', '07', '08', '09']:
                cofins = COFINSNT(
                    CST=item['cofins_cst_code']
                )
            elif item['cofins_cst_code'] == '03':
                raise NotImplementedError
                # vr_cofins_proprio
                cofins = COFINSQtde(
                    CST=item['cofins_cst_code'],
                    qBCProd=D(item['quantidade']).quantize(D('0.01')),
                    vAliqProd=D(item['vr_cofins_proprio']).quantize(D('0.01'))
                )
            elif item['cofins_cst_code'] == '99':
                cofins = COFINSOutr(
                    CST=item['cofins_cst_code'],
                    vBC=D(item['cofins_base'] * item['price_without_tax']).quantize(D('0.01')),
                    pCOFINS=al_cofins_proprio,
                )

        imposto = Imposto(
            vItem12741=D(item['amount_estimate_tax']).quantize(D('0.01')),
            icms=icms,
            pis=pis,
            cofins=cofins,
        )
        imposto.validar()

        detalhe = Detalhamento(
            produto=produto,
            imposto=imposto,
        )
        detalhe.validar()
        return detalhe, estimated_taxes

    def __prepare_payment(self, json):
        kwargs = {}
        if json['sat_card_accrediting']:
            kwargs['cAdmC'] = json['sat_card_accrediting']
        pagamento = MeioPagamento(
            cMP=json['sat_payment_mode'],
            vMP=D(json['amount']).quantize(
                TWOPLACES),
            **kwargs
        )
        pagamento.validar()
        return pagamento

    def __prepare_send_cfe(self, json):
        detalhamentos = []
        total_taxes = D(0)
        for item in json['orderlines']:
            detalhe, estimated_taxes = self.__prepare_send_detail_cfe(item)
            detalhamentos.append(detalhe)
            total_taxes += estimated_taxes

        # descontos_acrescimos_subtotal = DescAcrEntr(
        #     vCFeLei12741=total_taxes)
        # descontos_acrescimos_subtotal.validar()

        pagamentos = []
        for pagamento in json['paymentlines']:
            pagamentos.append(self.__prepare_payment(pagamento))

        kwargs = {}
        if json['client']:
            # TODO: Verificar se tamanho == 14: cnpj
            kwargs['destinatario'] = Destinatario(CPF=json['client'])
        emitente = Emitente(
            CNPJ=punctuation_rm(json['company']['cnpj']),
            IE=punctuation_rm(json['company']['ie']),
            indRatISSQN='N')
        emitente.validar()
        return CFeVenda(
            CNPJ=punctuation_rm(json['company']['cnpj_software_house']),
            signAC=self.assinatura,
            numeroCaixa=2,
            emitente=emitente,
            detalhamentos=detalhamentos,
            pagamentos=pagamentos,
            vCFeLei12741=total_taxes,
            **kwargs
        )

    def _send_cfe(self, json):
        try:
            resposta = self.device.enviar_dados_venda(
                self.__prepare_send_cfe(json))
            self._print_extrato_venda(resposta.arquivoCFeSAT)
            return {
                'xml': resposta.arquivoCFeSAT,
                'numSessao': resposta.numeroSessao,
                'chave_cfe': resposta.chaveConsulta,
            }
        except Exception as e:
            if hasattr(e, 'resposta'):
                return e.resposta.mensagem
            elif hasattr(e, 'message'):
                return e.message
            else:
                return "Erro ao validar os dados para o xml! " \
                       "Contate o suporte técnico."

    def __prepare_cancel_cfe(self, chCanc, cnpj, doc_destinatario):
        kwargs = {}
        if doc_destinatario:
            kwargs['destinatario'] = Destinatario(CPF=punctuation_rm(doc_destinatario))
        return CFeCancelamento(
            chCanc=chCanc,
            CNPJ=punctuation_rm(cnpj),
            signAC=self.assinatura,
            numeroCaixa=2,
            **kwargs
        )

    def _cancel_cfe(self, order):
        try:
            resposta = self.device.cancelar_ultima_venda(
                order['chaveConsulta'],
                self.__prepare_cancel_cfe(
                    order['chaveConsulta'], order['cnpj_software_house']
                )
            )
            self._print_extrato_cancelamento(
                order['xml_cfe_venda'], resposta.arquivoCFeBase64)
            return {
                'order_id': order['order_id'],
                'xml': resposta.arquivoCFeBase64,
                'numSessao': resposta.numeroSessao,
                'chave_cfe': resposta.chaveConsulta,
            }
        except Exception as e:
            if hasattr(e, 'resposta'):
                return e.resposta.mensagem
            elif hasattr(e, 'message'):
                return e.message
            else:
                return "Erro ao validar os dados para o xml! " \
                       "Contate o suporte técnico."

    def action_call_sat(self, task, json=False):

        _logger.info('SAT: Task {0}'.format(task))

        try:
            with self.satlock:
                if task == 'connect':
                    pass
                elif task == 'get_device':
                    return self._get_device()
                elif task == 'reprint':
                    return self._reprint_cfe(json)
                elif task == 'send':
                    return self._send_cfe(json)
                elif task == 'cancel':
                    return self._cancel_cfe(json)
        except ErroRespostaSATInvalida as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}
        except ExcecaoRespostaSAT as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}
        except Exception as ex:
            _logger.error('SAT Error: {0}'.format(ex))
            return {'excessao': ex}

    def _init_printer(self):
        if not self.impressora:
            return False

        if self.fiscal_printer_type == 'NetworkConnection':
            from escpos.conn.network import NetworkConnection as Connection
            conn = Connection(host=self.printer_params, port=9100)
        elif self.fiscal_printer_type == 'BluetoothConnection':
            from escpos.conn.network import BluetoothConnection as Connection
        elif self.fiscal_printer_type == 'DummyConnection':
            from escpos.conn.network import DummyConnection as Connection
        elif self.fiscal_printer_type == 'FileConnection':
            from escpos.conn.network import FileConnection as Connection
        elif self.fiscal_printer_type == 'NetworkConnection':
            from escpos.conn.network import NetworkConnection as Connection
        elif self.fiscal_printer_type == 'SerialConnection':
            from escpos.conn.network import SerialConnection as Connection
            conn = Connection.parse(self.printer_params).get_connection()
        elif self.fiscal_printer_type == 'USBConnection':
            from escpos.conn.network import USBConnection as Connection

        if self.impressora == 'epson-tm-t20':
            _logger.info('SAT Impressao: Epson TM-T20')
            from escpos.impl.epson import TMT20 as Printer
        elif self.impressora == 'bematech-mp4200th':
            _logger.info('SAT Impressao: Bematech MP4200TH')
            from escpos.impl.bematech import MP4200TH as Printer
        elif self.impressora == 'daruma-dr700':
            _logger.info('SAT Impressao: Daruma Dr700')
            from escpos.impl.daruma import DR700 as Printer
        elif self.impressora == 'elgin-i9':
            _logger.info('SAT Impressao: Elgin I9')
            from escpos.impl.elgin import ElginI9 as Printer
        else:
            return False

        try:
            self.printer_conf = carregar('/odoo/sat/satextrato.ini')
            _logger.info('[HW FISCAL] Impressora - Carregada a configuração personalizada')
        except:
            self.printer_conf = padrao()
            _logger.info('[HW FISCAL] Impressora - Carregada a configuração padrão')

        printer = Printer(conn)

        from escpos import feature
        printer.hardware_features.update({
            feature.COLUMNS: feature.Columns(
                normal=42,
                expanded=24,
                condensed=56)
        })

        printer.init()
        _logger.info('[HW FISCAL] Impressora - Inicializada')
        return printer

    def _print_extrato_venda(self, xml):
        if not self.printer:
            _logger.info('[HW FISCAL] Impressora - Falha ao executar _print_extrato_venda')
            return False
        ExtratoCFeVenda(
            fp=io.StringIO(base64.b64decode(xml).decode('utf-8')), impressora=self.printer, config=self.printer_conf
        ).imprimir()
        _logger.info('[HW FISCAL] Impressora - OK - _print_extrato_venda')
        return True

    def _print_extrato_cancelamento(self, xml_venda, xml_cancelamento):
        if not self.printer:
            return False
        extrato = ExtratoCFeCancelamento(
            io.StringIO(base64.b64decode(xml_venda)),
            io.StringIO(base64.b64decode(xml_cancelamento)),
            self.printer
        )
        extrato.imprimir()
        return True

    def _reprint_cfe(self, json):
        if json['canceled_order']:
            return self._print_extrato_cancelamento(
                json['xml_cfe_venda'], json['xml_cfe_cacelada'])
        else:
            return self._print_extrato_venda(json['xml_cfe_venda'])

    def run(self):
        self.device = None
        while True:
            if self.device:
                self.status_sat()
                time.sleep(40)
            else:
                self.device = self.action_call_sat('get_device')
                if not self.device:
                    time.sleep(40)


class SatDriver(hw_proxy.Proxy):

    # TODO: Temos um problema quando o sat é iniciado depois do POS
    # @http.route('/hw_proxy/status_json', type='json', auth='none', cors='*')
    # def status_json(self):
    #     if not hw_proxy.drivers['satcfe'].device:
    #         hw_proxy.drivers['satcfe'].get_device()
    #     return self.get_status()

    @http.route('/hw_proxy/init/', type='json', auth='none', cors='*')
    def init(self, json):
        hw_proxy.drivers['hw_fiscal'] = Sat(**json)
        return True

    @http.route('/hw_proxy/enviar_cfe_sat/', type='json', auth='none', cors='*')
    def enviar_cfe_sat(self, json):
        _logger.info(json)
        return hw_proxy.drivers['hw_fiscal'].action_call_sat('send', json)

    @http.route('/hw_proxy/cancelar_cfe/', type='json', auth='none', cors='*')
    def cancelar_cfe(self, json):
        return hw_proxy.drivers['hw_fiscal'].action_call_sat('cancel', json)

    @http.route('/hw_proxy/reprint_cfe/', type='json', auth='none', cors='*')
    def reprint_cfe(self, json):
        return hw_proxy.drivers['hw_fiscal'].action_call_sat('reprint', json)
