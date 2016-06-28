# -*- coding: utf-8 -*-
import logging
import time
from threading import Thread, Lock
from requests import ConnectionError
from decimal import Decimal
import base64

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
    cliente = ClienteSATLocal(
        BibliotecaSAT('/opt/sat/tanca/libsat64.so'),
        codigo_ativacao='12345678'
    )
    # cliente = ClienteSATHub('localhost', 5000, numero_caixa=1)
except ImportError:
    _logger.error('Odoo module hw_l10n_br_pos depends on the satcfe module')
    satcfe = None




TWOPLACES = Decimal(10) ** -2
FOURPLACES = Decimal(10) ** -4


class Sat(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.lock = Lock()
        self.satlock = Lock()
        self.status = {'status': 'connecting', 'messages': []}
        self.input_dir = '/dev/serial/by-path/'
        self.device = None
        self.probed_device_paths = []
        self.path_to_scale = ''

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

    def get_device(self):

        try:
            if cliente.consultar_sat():

                self.set_status('connected', 'Connected to SAT')

                return cliente
        except ErroRespostaSATInvalida as ex_sat_invalida:
            # o equipamento retornou uma resposta que não faz sentido;
            # loga, e lança novamente ou lida de alguma maneira
            self.set_status('disconnected', 'SAT Not Found')
            return None
        except ExcecaoRespostaSAT as ex_resposta:
            self.set_status('disconnected', 'SAT Not Found')
            return None
        except ConnectionError as ex_conn_error:
            pass
        except Exception as ex:
            self.set_status('error', str(ex))
            return None

    def status_sat(self):
        with self.satlock:
            if self.device:
                try:
                    if cliente.consultar_sat():

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

    def printExtratoCFeVenda(self, config, arquivoCFeSAT):
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
        conn = SerialSettings.as_from(
            config['printer_params']).get_connection()
        printer = Printer(conn)
        printer.init()
        extrato = ExtratoCFeVenda(arquivoCFeSAT, printer)
        extrato.imprimir()

    def montar_cfe(self, json):
        detalhamentos = []

        for item in json['orderlines']:
            detalhamentos.append(
                Detalhamento(
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
                        cofins=COFINSSN(CST='49'))),
            )

        cfe = CFeVenda(
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
        return cfe

    def sat(self, json):
        resposta = None
        json_salvar_cfe = {
            'xml': '',
            'chaveCfe': '',
            'numSessao': '',
            'chave_cfe': '',
            'excessao': False
        }

        try:
            resposta = cliente.enviar_dados_venda(self.montar_cfe(json))
            json_salvar_cfe = {
                'xml': resposta.arquivoCFeSAT,
                'numSessao': resposta.numeroSessao,
                'chave_cfe': resposta.chaveConsulta
            }
            if resposta.arquivoCFeSAT and json['configs_sat']['impressora']:
                self.printExtratoCFeVenda(json['configs_sat'],
                                          resposta.arquivoCFeSAT)
        except ErroRespostaSATInvalida as ex_sat_invalida:
            json_salvar_cfe = {
                'excessao': ex_sat_invalida
            }

        except ExcecaoRespostaSAT as ex_resposta:
            json_salvar_cfe = {
                'excessao': ex_resposta
            }

        except Exception as ex:
            json_salvar_cfe = {
                'excessao': ex
            }

        return json_salvar_cfe

    def montar_xml_cfe_cancelamento(self, chCanc):
        cfecanc = CFeCancelamento(
            chCanc=chCanc,
            CNPJ='16716114000172',
            signAC=constantes.ASSINATURA_AC_TESTE,
            numeroCaixa=2
        )
        return cfecanc

    def sat_cancelar_cfe(self, chave_cfe):
        try:
            resposta = cliente.cancelar_ultima_venda(
                chave_cfe,
                self.montar_xml_cfe_cancelamento(chave_cfe)
            )
            return True
        except ErroRespostaSATInvalida as ex_sat_invalida:
            json_cfe = {
                'excessao': ex_sat_invalida
            }
            return json_cfe
        except ExcecaoRespostaSAT as ex_resposta:
            json_cfe = {
                'excessao': ex_resposta
            }
            return json_cfe
        except Exception as ex:
            json_cfe = {
                'excessao': ex
            }

        return json_cfe

    def run(self):
        self.device = None
        while True:
            if self.device:
                self.status_sat()
                time.sleep(2)
            else:
                with self.satlock:
                    self.device = self.get_device()
                if not self.device:
                    time.sleep(1)


sat_thread = None
if satcfe:
    sat_thread = Sat()
    hw_proxy.drivers['satcfe'] = sat_thread
    

class SatDriver(hw_proxy.Proxy):
    @http.route('/hw_proxy/init/', type='json', auth='none', cors='*')
    def sat_init(self):
        if sat_thread:
            Sat.status_sat()
            Sat.device = 'SAT'
            _logger.info('SAT: STATUS')
            return True
        return None

    @http.route('/hw_proxy/enviar_cfe_sat/', type='json', auth='none', cors='*')
    def enviar_cfe_sat(self, json):
        if sat_thread:
            if sat_thread.status['status'] == 'connected':
                _logger.info('SAT: Enviando CFE')
                return sat_thread.sat(json)
            return False

    @http.route('/hw_proxy/cancelar_cfe/', type='json', auth='none', cors='*')
    def cancelar_cfe(self, chave_cfe):
        if sat_thread:
            if sat_thread.status['status'] == 'connected':
                _logger.info('SAT: Cancelando CFE')
                return sat_thread.sat_cancelar_cfe(chave_cfe)
            return False

