"""
Módulo para consulta histórica com gráficos usando TimeSeriesGraph
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.properties import StringProperty, ListProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from datetime import datetime, timedelta
from timeseriesgraph import TimeSeriesGraph
from tags import ALL_TAGS
import math
from kivy.graphics import Color, Rectangle, Line


class GraficoHistorico(TimeSeriesGraph):
    """Gráfico histórico personalizado"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.xlabel = 'Tempo'
        self.ylabel = 'Valor'
        self.x_grid_label = True
        self.y_grid_label = True
        self.x_grid = True
        self.y_grid = True
        self.padding = dp(10)
        self.x_ticks_major = 5
        self.y_ticks_major = 5
        self.ymin = 0
        self.ymax = 100
        self._data_points = []
        self._timestamps = []
        self._valores_originais = []  # Para armazenar os valores originais
        self._tempos_originais = []   # Para armazenar os tempos originais
        
        # Configurações para valores fixos no eixo Y
        self._y_labels_fixed = True  # Manter labels fixos
        self._y_min_fixed = None
        self._y_max_fixed = None
        
    def adicionar_dados(self, timestamps, valores, label="Dados"):
        """Adiciona dados ao gráfico"""
        self.clearPlots()
        self._data_points = []
        self._timestamps = []
        self._valores_originais = valores.copy() if valores else []
        self._tempos_originais = timestamps.copy() if timestamps else []
        
        if not timestamps or not valores:
            return
            
        # Adicionar plot
        from kivy_garden.graph import LinePlot
        plot = LinePlot(color=[0, 0.5, 1, 1], line_width=1.5)
        self.add_plot(plot)
        
        # Processar dados
        for i, (ts, val) in enumerate(zip(timestamps, valores)):
            if val is not None:
                self._data_points.append((i, val))
                self._timestamps.append(datetime.fromtimestamp(ts))
                
        plot.points = self._data_points
        
        # Configurar limites do eixo Y com valores fixos e decentes
        self._configurar_limites_fixos(valores)
        
        self.xmax = len(self._data_points) - 1 if self._data_points else 10
        self.xmin = 0
        
        # Atualizar labels de tempo
        self.update_x_labels(self._timestamps)
        
    def _configurar_limites_fixos(self, valores):
        """Configura limites fixos e decentes para o eixo Y"""
        if valores:
            valores_validos = [v for v in valores if v is not None]
            if valores_validos:
                min_val = min(valores_validos)
                max_val = max(valores_validos)
                
                # Se todos os valores forem iguais, criar um intervalo
                if min_val == max_val:
                    min_val = min_val - abs(min_val * 0.1) if min_val != 0 else -1
                    max_val = max_val + abs(max_val * 0.1) if max_val != 0 else 1
                
                # Arredondar para valores "bonitos"
                from math import log10, floor
                
                def round_to_nice(value):
                    """Arredonda para um valor 'bonito' (1, 2, 5, 10, etc.)"""
                    if value == 0:
                        return 0
                    magnitude = 10 ** floor(log10(abs(value)))
                    normalized = abs(value) / magnitude
                    
                    # Valores bonitos: 1, 2, 5, 10
                    if normalized < 1.5:
                        nice = 1
                    elif normalized < 3:
                        nice = 2
                    elif normalized < 7:
                        nice = 5
                    else:
                        nice = 10
                    
                    result = nice * magnitude
                    return result if value >= 0 else -result
                
                # Calcular intervalo e arredondar
                intervalo = max_val - min_val
                intervalo_nice = round_to_nice(intervalo * 1.2)
                
                # Centralizar os dados
                centro = (max_val + min_val) / 2
                
                self.ymin = centro - intervalo_nice / 2
                self.ymax = centro + intervalo_nice / 2
                
                # Garantir que os dados caibam dentro dos limites
                if min_val < self.ymin:
                    self.ymin = min_val - abs(min_val * 0.1)
                if max_val > self.ymax:
                    self.ymax = max_val + abs(max_val * 0.1)
                
                # Armazenar limites fixos
                self._y_min_fixed = self.ymin
                self._y_max_fixed = self.ymax
                
                # Configurar ticks maiores baseados no intervalo
                self.y_ticks_major = self._calcular_ticks_major(intervalo_nice)
                
    def _calcular_ticks_major(self, intervalo):
        """Calcula um número adequado de ticks maiores para o eixo Y"""
        if intervalo > 1000:
            return intervalo / 200  # Para grandes intervalos
        elif intervalo > 100:
            return intervalo / 50
        elif intervalo > 10:
            return intervalo / 10
        else:
            return intervalo / 5
            
    def atualizar_labels_eixo_y(self, unidade):
        """Atualiza o label do eixo Y com a unidade"""
        self.ylabel = f'Valor ({unidade})'
        
    def limpar_grafico(self):
        """Limpa o gráfico"""
        self.clearPlots()
        self._data_points = []
        self._timestamps = []
        self._valores_originais = []
        self._tempos_originais = []
        self.ymin = 0
        self.ymax = 100
        self.ylabel = 'Valor'
        self._y_min_fixed = None
        self._y_max_fixed = None
        

    def _on_zoom(self, instance, value):
        """Override do zoom para não afetar labels"""
        # Primeiro, executar o comportamento padrão
        super()._on_zoom(instance, value)
        
        # DEPOIS, reaplicar nossos labels fixos
        if self._time_labels_fixed:
            self._aplicar_labels_fixos()

class ControlesGrafico(BoxLayout):
    """Controles para o gráfico histórico"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(50)
        self.spacing = dp(10)
        self.padding = [dp(10), dp(5)]
        
        # Botão Zoom In
        self.btn_zoom_in = Button(
            text="+ Zoom",
            size_hint=(None, 1),
            width=dp(100),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        
        # Botão Zoom Out
        self.btn_zoom_out = Button(
            text="- Zoom",
            size_hint=(None, 1),
            width=dp(100),
            background_color=(0.8, 0.6, 0.2, 1)
        )
        
        # Botão Reset - Vamos melhorar este
        self.btn_reset = Button(
            text="Resetar Vista",
            size_hint=(None, 1),
            width=dp(120),
            background_color=(0.6, 0.2, 0.8, 1)
        )
        
        # Espaçador
        espacador = Label(size_hint=(1, 1))
        
        # Adicionar widgets
        self.add_widget(self.btn_zoom_in)
        self.add_widget(self.btn_zoom_out)
        self.add_widget(self.btn_reset)
        self.add_widget(espacador)

class FormularioConsulta(BoxLayout):
    """Formulário para seleção de parâmetros da consulta"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(15)
        self.size_hint_y = None
        self.height = dp(230)  # Reduzi um pouco a altura
        
        # Título da seção
        titulo = Label(
            text="Consulta de Dados Históricos",
            size_hint_y=None,
            height=dp(30),
            font_size='16sp',
            bold=True
        )
        self.add_widget(titulo)
        
        # Linha 1: Seleção de tag
        linha_tag = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        linha_tag.add_widget(Label(
            text="Variável:",
            size_hint_x=None,
            width=dp(80)
        ))
        
        self.spinner_tag = Spinner(
            text='Selecione uma tag',
            values=list(ALL_TAGS.keys()),
            size_hint_x=0.7
        )
        linha_tag.add_widget(self.spinner_tag)
        self.add_widget(linha_tag)
        
        # Linha 2: Datas Início e Fim lado a lado
        linha_datas = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(20)
        )
        
        # Coluna Início
        col_inicio = BoxLayout(orientation='vertical', spacing=dp(2))
        col_inicio.add_widget(Label(
            text="Início:",
            size_hint_y=None,
            height=dp(20),
            font_size='12sp'
        ))
        dt_inicio = datetime.now() - timedelta(hours=1)
        self.input_inicio = TextInput(
            text=dt_inicio.strftime("%d/%m/%Y %H:%M"),
            multiline=False,
            hint_text="DD/MM/AAAA HH:MM",
            size_hint_y=None,
            height=dp(35),
            font_size='14sp'
        )
        col_inicio.add_widget(self.input_inicio)
        linha_datas.add_widget(col_inicio)
        
        # Coluna Fim
        col_fim = BoxLayout(orientation='vertical', spacing=dp(2))
        col_fim.add_widget(Label(
            text="Fim:",
            size_hint_y=None,
            height=dp(20),
            font_size='12sp'
        ))
        dt_fim = datetime.now()
        self.input_fim = TextInput(
            text=dt_fim.strftime("%d/%m/%Y %H:%M"),
            multiline=False,
            hint_text="DD/MM/AAAA HH:MM",
            size_hint_y=None,
            height=dp(35),
            font_size='14sp'
        )
        col_fim.add_widget(self.input_fim)
        linha_datas.add_widget(col_fim)
        
        self.add_widget(linha_datas)
        
        # Linha 3: Consulta Rápida
        linha_rapida = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        linha_rapida.add_widget(Label(
            text="Consulta Rápida:",
            size_hint_x=None,
            width=dp(120)
        ))
        
        # Container para botões rápidos
        botoes_rapidos = BoxLayout(spacing=dp(5))
        for periodo in ['1h', '6h', '24h', '7d']:
            btn = Button(
                text=periodo,
                size_hint_x=0.2
            )
            btn.periodo = periodo  # Atributo personalizado
            botoes_rapidos.add_widget(btn)
            
        linha_rapida.add_widget(botoes_rapidos)
        self.add_widget(linha_rapida)
        
        # Armazenar referência para callbacks
        self.botoes_rapidos = botoes_rapidos
        
    def obter_parametros(self):
        """Retorna os parâmetros do formulário"""
        return {
            'tag': self.spinner_tag.text,
            'inicio': self.input_inicio.text,
            'fim': self.input_fim.text
        }
        
    def definir_periodo_rapido(self, horas):
        """Define um período rápido baseado em horas atrás"""
        fim = datetime.now()
        inicio = fim - timedelta(hours=horas)
        
        self.input_inicio.text = inicio.strftime("%d/%m/%Y %H:%M")
        self.input_fim.text = fim.strftime("%d/%m/%Y %H:%M")
    
class ConsultaHistoricoPopup(Popup):
    """Popup principal de consulta histórica"""
    
    def __init__(self, bd_handler, **kwargs):
        super().__init__(**kwargs)
        self.title = "Consulta de Dados Históricos"
        self.size_hint = (0.95, 0.95)
        self.bd_handler = bd_handler
        
        # Layout principal
        layout_principal = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # Formulário de consulta (datas lado a lado)
        self.formulario = FormularioConsulta()
        layout_principal.add_widget(self.formulario)
        
        # Configurar callbacks para botões rápidos
        for btn in self.formulario.botoes_rapidos.children:
            btn.bind(on_press=self._on_botao_rapido_pressed)
        
        # Separador visual
        separador = BoxLayout(size_hint_y=None, height=dp(1))
        separador.canvas.before.clear()
        with separador.canvas.before:
            Color(0.7, 0.7, 0.7, 1)
            Rectangle(pos=separador.pos, size=separador.size)
        layout_principal.add_widget(separador)
        
        # Controles de ação
        controles_acao = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            spacing=dp(15),
            padding=[dp(20), dp(10)]
        )
        
        btn_consultar = Button(
            text="Consultar",
            size_hint_x=0.4,
            background_color=(0.2, 0.6, 0.8, 1),
            font_size='14sp'
        )
        btn_consultar.bind(on_press=self.realizar_consulta)
        
        btn_limpar = Button(
            text="Limpar",
            size_hint_x=0.3,
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='14sp'
        )
        btn_limpar.bind(on_press=self.limpar_grafico)
        
        btn_fechar = Button(
            text="Fechar",
            size_hint_x=0.3,
            font_size='14sp'
        )
        btn_fechar.bind(on_press=self.dismiss)
        
        controles_acao.add_widget(btn_consultar)
        controles_acao.add_widget(btn_limpar)
        controles_acao.add_widget(btn_fechar)
        
        layout_principal.add_widget(controles_acao)
        
        # Área do gráfico (MAIOR - aproveitando espaço economizado)
        self.grafico = GraficoHistorico(
            size_hint=(1, 0.75),  # Aumentei significativamente a altura
            x_ticks_major=10,
            y_ticks_major=5
        )
        layout_principal.add_widget(self.grafico)
        
        # Controles do gráfico
        self.controles_grafico = ControlesGrafico()
        self.controles_grafico.btn_zoom_in.bind(on_press=self.zoom_in)
        self.controles_grafico.btn_zoom_out.bind(on_press=self.zoom_out)
        self.controles_grafico.btn_reset.bind(on_press=self.reset_zoom)
        
        layout_principal.add_widget(self.controles_grafico)
        
        # Barra de status simples
        self.status_bar = Label(
            text="Pronto para consultar",
            size_hint_y=None,
            height=dp(25),
            font_size='11sp',
            color=(0.3, 0.3, 0.3, 1)
        )
        layout_principal.add_widget(self.status_bar)
        
        self.content = layout_principal
        
        # Bind para redimensionamento
        self.bind(size=self._atualizar_layout)
        
    def _atualizar_layout(self, instance, value):
        """Atualiza layout quando o tamanho muda"""
        # Ajustar altura do formulário se necessário
        pass
        
    def _on_botao_rapido_pressed(self, instance):
        """Lida com cliques nos botões de consulta rápida"""
        periodos = {
            '1h': 1,
            '6h': 6,
            '24h': 24,
            '7d': 168  # 7 dias em horas
        }
        
        if instance.periodo in periodos:
            self.formulario.definir_periodo_rapido(periodos[instance.periodo])
            self.status_bar.text = f"Período definido: {instance.text}"
            
    def parse_datetime(self, texto):
        """Converte texto para timestamp"""
        try:
            # Tentar formato com hora
            dt = datetime.strptime(texto, "%d/%m/%Y %H:%M")
        except ValueError:
            try:
                # Tentar formato sem hora
                dt = datetime.strptime(texto, "%d/%m/%Y")
            except ValueError:
                try:
                    # Tentar formato alternativo
                    dt = datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    return None
        return dt
        
    def realizar_consulta(self, instance):
        """Realiza a consulta no banco de dados"""
        try:
            # Obter parâmetros do formulário
            self.status_bar.text = "Consultando dados..."
            params = self.formulario.obter_parametros()
            
            # Validar tag
            if params['tag'] == 'Selecione uma tag':
                self.mostrar_erro("Por favor, selecione uma variável")
                return
                
            # Validar e converter datas
            dt_inicio = self.parse_datetime(params['inicio'])
            dt_fim = self.parse_datetime(params['fim'])
            
            if not dt_inicio or not dt_fim:
                self.mostrar_erro("Formato de data/hora inválido. Use DD/MM/AAAA HH:MM")
                return
                
            if dt_fim <= dt_inicio:
                self.mostrar_erro("A data final deve ser posterior à data inicial")
                return
                
            # Mapear tag para campo do banco
            campo_db = self.mapear_tag_para_campo(params['tag'])
            if not campo_db:
                self.mostrar_erro(f"A tag '{params['tag']}' não está disponível no banco de dados")
                return
                
            # Obter informações da tag
            tag_info = ALL_TAGS.get(params['tag'])
            if not tag_info:
                self.mostrar_erro(f"Informações não encontradas para a tag '{params['tag']}'")
                return
                
            # Consultar banco de dados
            resultados = self.bd_handler.get_history(
                campo_db,
                dt_inicio,
                dt_fim
            )
            
            if not resultados:
                self.mostrar_erro("Nenhum dado encontrado para o período selecionado")
                return
                
            # Processar resultados
            timestamps = []
            valores = []
            
            for ts, valor in resultados:
                if valor is not None:
                    timestamps.append(ts.timestamp())
                    valores.append(float(valor))
                    
            if not timestamps:
                self.mostrar_erro("Nenhum dado válido encontrado")
                return
                
            # Atualizar gráfico
            self.grafico.adicionar_dados(timestamps, valores, tag_info.label)
            self.grafico.atualizar_labels_eixo_y(tag_info.unit)
            
            # Atualizar título
            self.title = f"Histórico: {tag_info.label} ({dt_inicio.strftime('%d/%m/%Y')} - {dt_fim.strftime('%d/%m/%Y')})"
            
            # Atualizar status bar se existir
            if hasattr(self, 'status_bar'):
                self.status_bar.text = f"✅ {len(valores)} pontos carregados"
            
        except Exception as e:
            self.mostrar_erro(f"Erro ao realizar consulta: {str(e)}")

            self.status_bar.text = f"{len(valores)} pontos carregados"
        
    def mapear_tag_para_campo(self, tag):
        """
        Mapeia o nome da tag para o campo correspondente no banco de dados
        """
        mapeamento = {
        # TAGS DE PROCESSO
        "co.temp_enrol_r":      "temp_enrol_r",
        "co.temp_carcaca":      "temp_carcaca",
        "co.vel_saida_ar":      "vel_saida_ar",
        "co.press_tubo_azul":   "press_tubo_azul",
        "co.torque":            "torque",
        "co.pressao":           "pressao",
        "co.vazao":             "vazao",
        "co.press_reservatorio":"press_reservatorio",
        "co.vazao_ramo_v01":    "vazao_ramo_v01",
        "co.med_torque":        "med_torque",
        
        # TAGS ELÉTRICAS - TENSÕES FASE-NEUTRO
        "co.v_rn": "v_rn",
        "co.v_sn": "v_sn",
        "co.v_tn": "v_tn",
        
        # TENSÕES FASE-FASE
        "co.v_rs": "v_rs",
        "co.v_st": "v_st",
        "co.v_tr": "v_tr",
        
        # POTÊNCIAS ATIVA POR FASE
        "co.p_kw_r":     "p_kw_r",
        "co.p_kw_s":     "p_kw_s",
        "co.p_kw_t":     "p_kw_t",
        "co.p_kw_total": "p_kw_total",
        
        # CORRENTES POR FASE
        "co.i_r":     "i_r",
        "co.i_s":     "i_s",
        "co.i_t":     "i_t",
        "co.i_n":     "i_n",
        "co.i_media": "i_media",
        }
        return mapeamento.get(tag)
        
    def zoom_in(self, instance):
        """Aumenta o zoom no eixo Y"""
        delta_y = (self.grafico.ymax - self.grafico.ymin) * 0.2
        self.grafico.ymin += delta_y / 2
        self.grafico.ymax -= delta_y / 2
        
        # Garantir que não inverta os limites
        if self.grafico.ymax <= self.grafico.ymin:
            self.grafico.ymax = self.grafico.ymin + 0.1
            
        self.status_bar.text = "Zoom aumentado"
        
    def zoom_out(self, instance):
        """Diminui o zoom no eixo Y"""
        delta_y = (self.grafico.ymax - self.grafico.ymin) * 0.2
        self.grafico.ymin = max(0, self.grafico.ymin - delta_y / 2)
        self.grafico.ymax += delta_y / 2
        
        self.status_bar.text = "Zoom diminuído"
        
    def reset_zoom(self, instance):
        """Reseta o zoom do gráfico"""
        if hasattr(self.grafico, 'resetar_vista'):
            self.grafico.resetar_vista()
            self.status_bar.text = "Vista resetada para ajuste automático"
        else:
            # Fallback: usar método antigo
            if self.grafico._data_points:
                valores = [p[1] for p in self.grafico._data_points if p[1] is not None]
                if valores:
                    min_val = min(valores)
                    max_val = max(valores)
                    margin = (max_val - min_val) * 0.1
                    self.grafico.ymin = min_val - margin if min_val - margin < min_val else min_val * 0.9
                    self.grafico.ymax = max_val + margin if max_val + margin > max_val else max_val * 1.1
                    self.status_bar.text = "Zoom resetado"

    def limpar_grafico(self, instance):
        """Limpa o gráfico"""
        self.grafico.limpar_grafico()
        self.status_bar.text = "Gráfico limpo"
        

    def mostrar_erro(self, mensagem):
        """Exibe uma mensagem de erro"""
        popup = Popup(
            title="Erro",
            content=Label(text=mensagem),
            size_hint=(0.6, 0.3)
        )
        popup.open()