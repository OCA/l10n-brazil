# -*- coding: utf-8 -*-
import logging
import time
from threading import Thread, Lock
from requests import ConnectionError
from decimal import Decimal
import StringIO
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http
import base64
import re, string

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
    from satcfe.entidades import ICMSSN102
    from satcfe.entidades import PISSN
    from satcfe.entidades import COFINSSN
    from satcfe.entidades import MeioPagamento
    from satcfe.entidades import CFeVenda
    from satcfe.entidades import CFeCancelamento
    from satcfe.excecoes import ErroRespostaSATInvalida
    from satcfe.excecoes import ExcecaoRespostaSAT
    from satextrato import ExtratoCFeVenda
    from satextrato import ExtratoCFeCancelamento

except ImportError:
    _logger.error('Odoo module hw_l10n_br_pos depends on the satcfe module')
    satcfe = None


TWOPLACES = Decimal(10) ** -2
FOURPLACES = Decimal(10) ** -4


def punctuation_rm(string_value):
    tmp_value = (
        re.sub('[%s]' % re.escape(string.punctuation), '', string_value or ''))
    return tmp_value

class Sat(Thread):
    def __init__(self, codigo_ativacao, sat_path, impressora, printer_params):
        Thread.__init__(self)
        self.codigo_ativacao = codigo_ativacao
        self.sat_path = sat_path
        self.impressora = impressora
        self.printer_params = printer_params
        self.lock = Lock()
        self.satlock = Lock()
        self.status = {'status': 'connecting', 'messages': []}
        self.printer = self._init_printer()
        self.device = self._get_device()

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
                    _logger.error('SAT Error: '+message)
                elif status == 'disconnected' and message:
                    _logger.warning('Disconnected SAT: '+message)
        else:
            self.status['status'] = status
            if message:
                self.status['messages'] = [message]
            else:
                self.status['messages'] = []

            if status == 'error' and message:
                _logger.error('SAT Error: '+message)
            elif status == 'disconnected' and message:
                _logger.warning('Disconnected SAT: '+message)

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
            kwargs['vDesc'] = Decimal((item['quantity'] * item['price']) -
                                      item['price_display']).quantize(TWOPLACES )

        return Detalhamento(
            produto=ProdutoServico(
                cProd=unicode(item['product_default_code']),
                xProd=item['product_name'],
                CFOP='5102',
                uCom=item['unit_name'],
                qCom=Decimal(item['quantity']).quantize(FOURPLACES),
                vUnCom=Decimal(item['price']).quantize(TWOPLACES),
                indRegra='A',
                NCM=punctuation_rm(item['fiscal_classification_id'][1]),
                **kwargs
                ),
            imposto=Imposto(
                icms=ICMSSN102(Orig=item['origin'], CSOSN='500'),
                pis=PISSN(CST='49'),
                cofins=COFINSSN(CST='49'))
        )

    def __prepare_payment(self, json):
        kwargs = {}
        if json['sat_card_accrediting']:
            kwargs['cAdmC'] = json['sat_card_accrediting']

        return MeioPagamento(
            cMP=json['sat_payment_mode'],
            vMP=Decimal(json['subtotal']).quantize(
                TWOPLACES)
            **kwargs
        )


    def __prepare_send_cfe(self, json):
        detalhamentos = []
        for item in json['orderlines']:
            detalhamentos.append(self.__prepare_send_detail_cfe(item))
        pagamentos = []
        for pagamento in json['paymentlines']:
            pagamentos.append(self.__prepare_payment(pagamento))

        kwargs = {}
        if json['client']:
            # TODO: Verificar se tamanho == 14: cnpj
            kwargs['destinatario'] = Destinatario(CPF=json['client'])

        return CFeVenda(
            CNPJ=json['company']['cnpj_software_house'],
            signAC=constantes.ASSINATURA_AC_TESTE,
            numeroCaixa=2,
            emitente=Emitente(
                CNPJ=json['company']['cnpj'],
                IE=json['company']['ie'],
                indRatISSQN='N'),
            detalhamentos=detalhamentos,
            pagamentos=pagamentos,
            **kwargs
        )

    def _send_cfe(self, json):
        resposta = self.device.enviar_dados_venda(
            self.__prepare_send_cfe(json))
        self._print_extrato_venda(resposta.arquivoCFeSAT)
        return {
            'xml': resposta.arquivoCFeSAT,
            'numSessao': resposta.numeroSessao,
            'chave_cfe': resposta.chaveConsulta,
        }

    def __prepare_cancel_cfe(self, chCanc):
        return CFeCancelamento(
            chCanc=chCanc,
            CNPJ='16716114000172',
            signAC=constantes.ASSINATURA_AC_TESTE,
            numeroCaixa=2
        )

    def _cancel_cfe(self, order):
        resposta = self.device.cancelar_ultima_venda(
            order['chaveConsulta'],
            self.__prepare_cancel_cfe(order['chaveConsulta'])
        )
        self._print_extrato_cancelamento(
            order['xml_cfe_venda'], resposta.arquivoCFeBase64)
        return {
            'order_id': order['order_id'],
            'xml': resposta.arquivoCFeBase64,
            'numSessao': resposta.numeroSessao,
            'chave_cfe': resposta.chaveConsulta,
        }

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

        from escpos.serial import SerialSettings

        if self.impressora == 'epson-tm-t20':
            _logger.info(u'SAT Impressao: Epson TM-T20')
            from escpos.impl.epson import TMT20 as Printer
        elif self.impressora == 'bematech-mp4200th':
            _logger.info(u'SAT Impressao: Bematech MP4200TH')
            from escpos.impl.bematech import MP4200TH as Printer
        elif self.impressora == 'daruma-dr700':
            _logger.info(u'SAT Impressao: Daruma Dr700')
            from escpos.impl.daruma import DR700 as Printer
        elif self.impressora == 'elgin-i9':
            _logger.info(u'SAT Impressao: Elgin I9')
            from escpos.impl.elgin import ElginI9 as Printer
        else:
            self.printer = False
        conn = SerialSettings.as_from(
            self.printer_params).get_connection()

        printer = Printer(conn)
        printer.init()
        return printer


    def _print_extrato_venda(self, xml):
        if not self.printer:
            return False
        extrato = ExtratoCFeVenda(
            StringIO.StringIO(base64.b64decode(xml)),
            self.printer
            )
        extrato.imprimir()
        return True

    def _print_extrato_cancelamento(self, xml_venda, xml_cancelamento):
        if not self.printer:
            return False
        extrato = ExtratoCFeCancelamento(
            StringIO.StringIO(base64.b64decode(xml_venda)),
            StringIO.StringIO(base64.b64decode(xml_cancelamento)),
            self.printer
            )
        extrato.imprimir()
        return True

    def _reprint_cfe(self, json):
        if json['canceled_order']:
            return self._print_extrato_cancelamento(
                json['xml_cfe_venda'], json['xml_cfe_cacelada'])
        else:
            return self._print_extrato_venda( json['xml_cfe_venda'])

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
        hw_proxy.drivers['satcfe'] = Sat(**json)
        return True

    @http.route('/hw_proxy/enviar_cfe_sat/', type='json', auth='none', cors='*')
    def enviar_cfe_sat(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('send', json)

    @http.route('/hw_proxy/cancelar_cfe/', type='json', auth='none', cors='*')
    def cancelar_cfe(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('cancel', json)

    @http.route('/hw_proxy/reprint_cfe/', type='json', auth='none', cors='*')
    def reprint_cfe(self, json):
        return hw_proxy.drivers['satcfe'].action_call_sat('reprint', json)
