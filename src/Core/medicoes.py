"""
Sistema de medições completo com cores ISA 101
"""

from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex


class MedicoesPopup(ModalView):
    """
    Popup de medições – apenas VISUAL.
    Lê dados do MainWidget e atualiza labels e cores.
    """

    tipo_medicao = StringProperty("temperaturas")
    titulo_atual = StringProperty("MEDIÇÕES EM TEMPO REAL")

    cor_botao_ativo = ListProperty([0.6, 0.6, 0.6, 1])
    cor_botao_inativo = ListProperty([0.8, 0.8, 0.8, 1])
    cor_texto_botao = ListProperty([0, 0, 0, 1])

    main_widget = ObjectProperty(None)

    def __init__(self, main_widget=None, **kwargs):
        self.main_widget = main_widget
        self.update_event = None

        kwargs.update({
            'size_hint': (0.9, 0.9),
            'auto_dismiss': False,
            'background_color': (1, 1, 1, 1),
            'overlay_color': (0, 0, 0, 0.5),
        })

        super().__init__(**kwargs)

        self.bind(on_open=self._iniciar_atualizacao)
        self.bind(on_dismiss=self._parar_atualizacao)

    def _iniciar_atualizacao(self, *args):
        self._atualizar_todos_valores()
        self.update_event = Clock.schedule_interval(
            lambda dt: self._atualizar_todos_valores(),
            1.0
        )

    def _parar_atualizacao(self, *args):
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def _atualizar_todos_valores(self):
        if not self.main_widget:
            return

        mw = self.main_widget

        # TEMPERATURAS
        self._atualizar_valor_e_cor('temp_carc_label', mw.co_temp_carc, '°C', 70, 85)
        self._atualizar_valor_e_cor('temp_r_label', mw.co_temp_r, '°C', 75, 90)

        # CORRENTES
        self._atualizar_valor_e_cor('corrente_r_label', mw.co_corrente_r, 'A', 20, 25)
        self._atualizar_valor_e_cor('corrente_s_label', mw.co_corrente_s, 'A', 20, 25)
        self._atualizar_valor_e_cor('corrente_t_label', mw.co_corrente_t, 'A', 20, 25)
        self._atualizar_valor_e_cor('corrente_n_label', mw.co_corrente_n, 'A', 2, 5)
        self._atualizar_valor_e_cor('corrente_media_label', mw.co_corrente_media, 'A', 20, 25)

        # TENSÕES
        self._atualizar_valor_e_cor('tensao_rs_label', mw.co_tensao_rs, 'V', 230, 240, tipo='tensao')
        self._atualizar_valor_e_cor('tensao_st_label', mw.co_tensao_st, 'V', 230, 240, tipo='tensao')
        self._atualizar_valor_e_cor('tensao_tr_label', mw.co_tensao_tr, 'V', 230, 240, tipo='tensao')
        # FP
        self._atualizar_valor_e_cor_fp('fp_r_label', mw.co_fp_r)
        self._atualizar_valor_e_cor_fp('fp_s_label', mw.co_fp_s)
        self._atualizar_valor_e_cor_fp('fp_t_label', mw.co_fp_t)
        self._atualizar_valor_e_cor_fp('fp_media_label', mw.co_fp_total)

        # THD
        self._atualizar_valor_e_cor_thd('thd_tensao_rs_label', mw.co_thd_tensao_rs, '%', 3, 5, 8)
        self._atualizar_valor_e_cor_thd('thd_tensao_st_label', mw.co_thd_tensao_st, '%', 3, 5, 8)
        self._atualizar_valor_e_cor_thd('thd_tensao_tr_label', mw.co_thd_tensao_tr, '%', 3, 5, 8)
        self._atualizar_valor_e_cor_thd('thd_corrente_r_label', mw.co_thd_corrente_r, '%', 5, 8, 12)
        self._atualizar_valor_e_cor_thd('thd_corrente_s_label', mw.co_thd_corrente_s, '%', 5, 8, 12)
        self._atualizar_valor_e_cor_thd('thd_corrente_t_label', mw.co_thd_corrente_t, '%', 5, 8, 12)
        self._atualizar_valor_e_cor_thd('thd_corrente_n_label', mw.co_thd_corrente_n, '%', 5, 8, 12)

    # ======================================================
    # MÉTODOS AUXILIARES PARA ATUALIZAÇÃO DOS DADOS
    # ======================================================

    def _atualizar_valor_e_cor(self, label_id, valor, unidade,
                               limite_amarelo, limite_vermelho, tipo='normal'):
        try:
            if hasattr(self, 'ids') and label_id in self.ids:
                label = self.ids[label_id]
                label.text = f"{valor:.1f} {unidade}"

                if tipo == 'tensao':
                    if 200 <= valor <= 230:
                        cor = "#008000"  # Verde
                    elif 230 < valor <= 240:
                        cor = "#FFD700"  # Amarelo
                    else:
                        cor = "#FF0000"  # Vermelho
                else:
                    if valor < limite_amarelo:
                        cor = "#008000"  # Verde
                    elif valor < limite_vermelho:
                        cor = "#FFD700"  # Amarelo
                    else:
                        cor = "#FF0000"  # Vermelho

                label.text_color = get_color_from_hex(cor)
        except Exception as e:
            print(f"Erro ao atualizar {label_id}: {e}")

    def _atualizar_valor_e_cor_fp(self, label_id, valor):
        try:
            if hasattr(self, 'ids') and label_id in self.ids:
                label = self.ids[label_id]
                label.text = f"{valor:.3f}"

                if valor >= 0.92:
                    cor = "#008000"  # Verde - excelente
                elif valor >= 0.85:
                    cor = "#FFD700"  # Amarelo - aceitável
                elif valor >= 0.8:
                    cor = "#FFA500"  # Laranja - ruim
                else:
                    cor = "#FF0000"  # Vermelho - crítico

                label.text_color = get_color_from_hex(cor)
        except Exception as e:
            print(f"Erro ao atualizar {label_id}: {e}")

    def _atualizar_valor_e_cor_thd(self, label_id, valor, unidade,
                                   limite_verde, limite_amarelo, limite_vermelho):
        try:
            if hasattr(self, 'ids') and label_id in self.ids:
                label = self.ids[label_id]
                label.text = f"{valor:.1f} {unidade}"

                if valor <= limite_verde:
                    cor = "#008000"  # Verde - excelente
                elif valor <= limite_amarelo:
                    cor = "#FFD700"  # Amarelo - aceitável
                elif valor <= limite_vermelho:
                    cor = "#FFA500"  # Laranja - ruim
                else:
                    cor = "#FF0000"  # Vermelho - crítico

                label.text_color = get_color_from_hex(cor)
        except Exception as e:
            print(f"Erro ao atualizar {label_id}: {e}")

    # ======================================================
    # MÉTODOS PARA FILTRAR OS TIPOS DE MEDIÇÃO
    # ======================================================

    def mostrar_temperaturas(self):
        self.tipo_medicao = "temperaturas"
        self.titulo_atual = "TEMPERATURAS"

    def mostrar_correntes(self):
        self.tipo_medicao = "correntes"
        self.titulo_atual = "CORRENTES"

    def mostrar_tensoes(self):
        self.tipo_medicao = "tensoes"
        self.titulo_atual = "TENSÕES"

    def mostrar_fator_potencia(self):
        self.tipo_medicao = "fator_potencia"
        self.titulo_atual = "FATOR DE POTÊNCIA"

    def mostrar_thd(self):
        self.tipo_medicao = "thd"
        self.titulo_atual = "THD (DISTORÇÃO HARMÔNICA)"

    def dismiss(self, *args, **kwargs):
        """Fecha o popup e para a atualização"""
        self._parar_atualizacao()
        super().dismiss(*args, **kwargs)
