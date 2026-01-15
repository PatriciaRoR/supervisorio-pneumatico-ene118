from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TagInfo:
    tag: str
    label: str
    unit: str
    vmin: float
    vmax: float


# Todas começam com "co." conforme orientação.
TAGS_PROCESSO = [
    TagInfo("co.temp_enrol_r", "Temperatura Enrolamento R", "°C", 0.0, 200.0),
    TagInfo("co.temp_carcaca", "Temperatura Carcaça", "°C", 0.0, 200.0),
    TagInfo("co.vel_saida_ar", "Velocidade de saída de ar", "RPM", 0.0, 3600.0),
    TagInfo("co.press_tubo_azul", "Pressão Tubo azul", "bar", 0.0, 12.0),
    TagInfo("co.torque", "Torque", "N·m", 0.0, 50.0),
    TagInfo("co.pressao", "Pressão", "bar", 0.0, 12.0),
    TagInfo("co.vazao", "Vazão", "Nm³/min", 0.0, 20.0),
    TagInfo("co.press_reservatorio", "Pressão no Reservatório", "bar", 0.0, 12.0),
    TagInfo("co.vazao_ramo_v01", "Vazão no Ramo da Válvula 01", "Nm³/min", 0.0, 20.0),
    TagInfo("co.med_torque", "Medida do Torque", "N·m", 0.0, 50.0),
]

TAGS_ELETRICAS = [
    TagInfo("co.v_rn", "Medida TDH tensão Fase R e Neutro", "V", 0.0, 300.0),
    TagInfo("co.v_sn", "Medida TDH tensão Fase S e Neutro", "V", 0.0, 300.0),
    TagInfo("co.v_tn", "Medida TDH tensão Fase T e Neutro", "V", 0.0, 300.0),

    TagInfo("co.v_rs", "Medida TDH tensão Fase R e Fase S", "V", 0.0, 520.0),
    TagInfo("co.v_st", "Medida TDH tensão Fase S e Fase T", "V", 0.0, 520.0),
    TagInfo("co.v_tr", "Medida TDH tensão Fase T e Fase R", "V", 0.0, 520.0),

    TagInfo("co.p_kw_r", "Potência ativa Fase R do Compressor", "W", 0.0, 6000.0),
    TagInfo("co.p_kw_s", "Potência ativa Fase S do Compressor", "W", 0.0, 6000.0),
    TagInfo("co.p_kw_t", "Potência ativa Fase T do Compressor", "W", 0.0, 6000.0),
    TagInfo("co.p_kw_total", "Potência ativa Total do Compressor", "W", 0.0, 18000.0),

    TagInfo("co.i_r", "Corrente na fase R do Compressor", "A", 0.0, 100.0),
    TagInfo("co.i_s", "Corrente na fase S do Compressor", "A", 0.0, 100.0),
    TagInfo("co.i_t", "Corrente na fase T do Compressor", "A", 0.0, 100.0),
    TagInfo("co.i_n", "Corrente no Neutro do Compressor", "A", 0.0, 50.0),
    TagInfo("co.i_media", "Corrente média do Compressor", "A", 0.0, 100.0),
]

ALL_TAGS = {t.tag: t for t in (TAGS_PROCESSO + TAGS_ELETRICAS)}
