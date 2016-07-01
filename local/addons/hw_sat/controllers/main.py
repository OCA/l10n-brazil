# -*- coding: utf-8 -*-
import logging
import time
from threading import Thread, Lock
from requests import ConnectionError
from decimal import Decimal
import openerp.addons.hw_proxy.controllers.main as hw_proxy
from openerp import http

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
        self.printer = False
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
        return Detalhamento(
            produto=ProdutoServico(
                cProd=unicode(int),
                xProd=item['product_name'],
                CFOP='5102',
                uCom=item['unit_name'],
                qCom=Decimal(item['quantity']).quantize(FOURPLACES),
                vUnCom=Decimal(item['price']).quantize(TWOPLACES),
                indRegra='A'),
            imposto=Imposto(
                icms=ICMSSN102(Orig='2', CSOSN='500'),
                pis=PISSN(CST='49'),
                cofins=COFINSSN(CST='49'))
        )

    def __prepare_send_cfe(self, json):
        detalhamentos = []
        for item in json['orderlines']:
            detalhamentos.append(self.__prepare_send_detail_cfe(item))

        return CFeVenda(
            CNPJ=json['company']['cnpj_software_house'],
            signAC=constantes.ASSINATURA_AC_TESTE,
            numeroCaixa=2,
            emitente=Emitente(
                CNPJ=json['company']['cnpj'],
                IE=json['company']['ie'],
                indRatISSQN='N'),
            detalhamentos=detalhamentos,
            pagamentos=[
                MeioPagamento(
                    cMP=constantes.WA03_DINHEIRO,
                    vMP=Decimal(json['subtotal']).quantize(
                        TWOPLACES)),
            ]
        )

    def _send_cfe(self, json):
        resposta = self.device.enviar_dados_venda(
            self.__prepare_send_cfe(json))
        self._print_extrato_venda(resposta.chaveConsulta, resposta.xml())
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

    def _cancel_cfe(self, chave_cfe):
        resposta = self.device.cancelar_ultima_venda(
            chave_cfe,
            self.__prepare_cancel_cfe(chave_cfe)
        )
        self._print_extrato_cancelamento(
            resposta.chaveConsulta, resposta.xml())
        return {
            'xml': resposta.arquivoCFeSAT,
            'numSessao': resposta.numeroSessao,
            'chave_cfe': resposta.chaveConsulta,
        }

    def action_call_sat(self, task, json=False):

        _logger.info('SAT: Task {0}'.format(task))

        try:

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
            _logger.error('SAT Error: '+ex)
            return {'excessao': ex}
        except ExcecaoRespostaSAT as ex:
            _logger.error('SAT Error: '+ex)
            return {'excessao': ex}
        except Exception as ex:
            _logger.error('SAT Error: '+ex)
            return {'excessao': ex}

    def _init_printer(self, config):
        from escpos.serial import SerialSettings

        if config['impressora'] == 'epson-tm-t20':
            _logger.info(u'SAT Impressao: Epson TM-T20')
            from escpos.impl.epson import TMT20 as Printer
        elif config['impressora'] == 'bematech-mp4200th':
            _logger.info(u'SAT Impressao: Bematech MP4200TH')
            from escpos.impl.bematech import MP4200TH as Printer
        elif config['impressora'] == 'daruma-dr700':
            _logger.info(u'SAT Impressao: Daruma Dr700')
            from escpos.impl.daruma import DR700 as Printer
        elif config['impressora'] == 'elgin-i9':
            _logger.info(u'SAT Impressao: Elgin I9')
            from escpos.impl.elgin import ElginI9 as Printer
        else:
            self.printer = False
        conn = SerialSettings.as_from(
            config['printer_params']).get_connection()
        self.printer = Printer(conn)
        self.printer.init()

    def _print_extrato_venda(self, chaveConsulta, xml):
        if not self.printer:
            return False
        file_path = '/tmp/' + chaveConsulta + '.xml'
        with open(file_path, 'w') as temp:
            temp.write(xml)
        with open(file_path, 'r') as fp:
            extrato = ExtratoCFeVenda(fp, self.printer)
            extrato.imprimir()
        return True

    def _print_extrato_cancelamento(self, chaveConsulta, xml):
        if not self.printer:
            return False
        file_path = '/tmp/' + chaveConsulta + '.xml'
        with open(file_path, 'w') as temp:
            temp.write(xml)
        with open(file_path, 'r') as fp:
            extrato = ExtratoCFeCancelamento(fp, self.printer)
            extrato.imprimir()
        return True

    def _reprint_cfe(self, json):
        if json['canceled_order']:
            return self._print_extrato_cancelamento(
                json['chave_cfe'], json['xml'])
        else:
            return self._print_extrato_venda(
                json['chave_cfe'], json['xml'])

    def run(self):
        self.device = None
        while True:
            if self.device:
                self.status_sat()
                time.sleep(2)
            else:
                with self.satlock:
                    self.device = self.action_call_sat('get_device')
                if not self.device:
                    time.sleep(1)


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
        return hw_proxy.drivers['satcfe'].action_call_sat('print', json)
