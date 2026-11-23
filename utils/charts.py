import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def criar_grafico_radar_habilidades(stats1: dict, stats2: dict, nome1: str, nome2: str):
    """Gera o Gráfico Radar comparando as 5 principais métricas de volume."""
    metricas = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']

    val1 = [stats1.get(m, 0) for m in metricas]
    val2 = [stats2.get(m, 0) for m in metricas]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=val1, theta=metricas, fill='toself', name=nome1,
        line_color='#1D428A', fillcolor='rgba(29, 66, 138, 0.4)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=val2, theta=metricas, fill='toself', name=nome2,
        line_color='#F58426', fillcolor='rgba(245, 132, 38, 0.4)'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showticklabels=True, gridcolor="#30363D")
        ),
        showlegend=True,
        title="🕸️ Perfil Comparativo de Habilidades",
        template='plotly_dark',
        height=380,
        margin=dict(l=30, r=30, t=50, b=30)
    )
    return fig


def criar_grafico_comparativo_barras(stats_p1: dict, stats_p2: dict, nome1: str, nome2: str):
    metricas = ['PPG', 'RPG', 'APG', 'SPG', 'BPG']
    v1 = [stats_p1.get(m, 0) for m in metricas]
    v2 = [stats_p2.get(m, 0) for m in metricas]

    fig = go.Figure(data=[
        go.Bar(name=nome1, x=metricas, y=v1, marker_color='#1D428A', text=v1, textposition='auto'),
        go.Bar(name=nome2, x=metricas, y=v2, marker_color='#F58426', text=v2, textposition='auto')
    ])
    fig.update_layout(
        barmode='group',
        title=f"📊 Volume Médio por Jogo: {nome1} vs {nome2}",
        template='plotly_dark',
        height=350,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def criar_grafico_eficiencia(stats_p1: dict, stats_p2: dict, nome1: str, nome2: str):
    metricas = ['FG%', '3P%', 'FT%']
    v1 = [stats_p1.get(m, 0) for m in metricas]
    v2 = [stats_p2.get(m, 0) for m in metricas]

    fig = go.Figure(data=[
        go.Bar(name=nome1, x=metricas, y=v1, marker_color='#1D428A', text=[f"{v}%" for v in v1], textposition='auto'),
        go.Bar(name=nome2, x=metricas, y=v2, marker_color='#F58426', text=[f"{v}%" for v in v2], textposition='auto')
    ])
    fig.update_layout(
        barmode='group',
        title="🎯 Eficiência de Arremessos (% de Acerto)",
        yaxis=dict(title="Porcentagem (%)", range=[0, 100]),
        template='plotly_dark',
        height=350,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig


def criar_grafico_evolucao_playoffs(df_playoffs: pd.DataFrame, nome_jogador: str):
    if df_playoffs.empty:
        return None
    fig = px.line(
        df_playoffs, x='SEASON_ID', y='PPG', text='PPG', markers=True,
        title=f"Média de Pontos por Jogo (PPG) em Playoffs — {nome_jogador}",
        labels={'SEASON_ID': 'Temporada', 'PPG': 'Pontos por Jogo'},
        template='plotly_dark'
    )
    fig.update_traces(line_color='#C8102E', marker=dict(size=8, color='#1D428A'), textposition="top center")
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20))
    return fig