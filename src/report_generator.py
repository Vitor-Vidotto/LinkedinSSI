"""
report_generator.py - Gerador de Relatório HTML Independente e Visual para o LinkedIn SSI.
Gera um documento HTML completo, responsivo, moderno e 100% offline (CSS embutido).
"""

import os
import html
from datetime import datetime
from typing import Optional
from .ssi_engine import SSIResult
from .recommendations import DiagnosticReport


def generate_html_report(result: SSIResult, report: DiagnosticReport, output_path: Optional[str] = None) -> str:
    """
    Gera um relatório HTML completo, estilizado e autocontido.
    Retorna o caminho absoluto do arquivo gerado.
    """
    m = result.metrics
    user_name = f"{m.first_name} {m.last_name}".strip() or "Profissional LinkedIn"
    ref_date_str = m.reference_date.strftime("%d/%m/%Y às %H:%M UTC")
    headline = html.escape(m.headline) if m.headline else "Perfil Profissional no LinkedIn"
    total_score = f"{result.total_score:.2f}"
    
    # Cores e estilos do score total
    if result.total_score >= 70:
        score_badge_bg = "#10B981"
        score_status = "Excelente"
    elif result.total_score >= 50:
        score_badge_bg = "#0A66C2"
        score_status = "Bom"
    elif result.total_score >= 40:
        score_badge_bg = "#F59E0B"
        score_status = "Moderado"
    else:
        score_badge_bg = "#EF4444"
        score_status = "Precisa de Atenção"

    # Geração dos cards dos 4 pilares
    pillars = [result.pillar_1, result.pillar_2, result.pillar_3, result.pillar_4]
    pillar_icons = {1: "👤", 2: "🔍", 3: "💡", 4: "🤝"}
    
    pillars_html = []
    for p in pillars:
        pct = (p.score / 25.0) * 100
        icon = pillar_icons.get(p.pillar_id, "📌")
        
        # Submétricas
        submetrics_html = []
        for s in p.submetrics:
            sub_pct = (s.score / s.max_score) * 100 if s.max_score > 0 else 0
            submetrics_html.append(f"""
            <div class="submetric-item">
                <div class="submetric-header">
                    <span class="submetric-name">{html.escape(s.name)}</span>
                    <span class="submetric-score"><strong>{s.score:.2f}</strong> / {s.max_score:.1f} pts</span>
                </div>
                <div class="progress-bar-container small">
                    <div class="progress-bar-fill" style="width: {min(100.0, max(0.0, sub_pct)):.1f}%; background-color: {p.color};"></div>
                </div>
                <div class="submetric-meta">
                    <span class="raw-value">📊 Dado: {html.escape(str(s.raw_value))}</span>
                </div>
                <p class="submetric-desc">{html.escape(s.description)}</p>
            </div>
            """)
        
        submetrics_block = "".join(submetrics_html)

        pillars_html.append(f"""
        <div class="pillar-card">
            <div class="pillar-header" style="border-left: 5px solid {p.color};">
                <div class="pillar-title-area">
                    <span class="pillar-icon">{icon}</span>
                    <div>
                        <h3 class="pillar-title">Pilar {p.pillar_id}: {html.escape(p.name)}</h3>
                        <span class="pillar-subtitle">{html.escape(p.name_en)}</span>
                    </div>
                </div>
                <div class="pillar-score-badge" style="background: {p.color};">
                    {p.score:.2f} / 25.00
                </div>
            </div>
            <div class="pillar-body">
                <div class="progress-info">
                    <span>Nível: <strong>{p.level}</strong></span>
                    <span>{pct:.1f}% do teto</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {min(100.0, max(0.0, pct)):.1f}%; background-color: {p.color};"></div>
                </div>
                
                <details class="submetrics-accordion">
                    <summary>Ver detalhamento das submétricas ({len(p.submetrics)} critérios)</summary>
                    <div class="submetrics-list">
                        {submetrics_block}
                    </div>
                </details>
            </div>
        </div>
        """)
    
    pillars_section = "\n".join(pillars_html)

    # Pontos Fortes e Gargalos
    strengths_html = "".join([f"<li><span class='icon check'>✔</span> {html.escape(s)}</li>" for s in report.strengths])
    bottlenecks_html = "".join([f"<li><span class='icon warn'>⚠</span> {html.escape(b)}</li>" for b in report.bottlenecks])

    # Ações recomendadas
    actions_html = []
    for a in report.actions:
        prio_class = "prio-alta" if a.priority == "Alta" else ("prio-media" if a.priority == "Média" else "prio-baixa")
        actions_html.append(f"""
        <tr class="action-row">
            <td><span class="prio-tag {prio_class}">{a.priority}</span></td>
            <td>
                <strong>{html.escape(a.title)}</strong>
                <div class="action-how">💡 <em>Como fazer:</em> {html.escape(a.how_to_do)}</div>
            </td>
            <td><span class="impact-badge">{html.escape(a.impact_estimate)}</span></td>
            <td class="action-pillar">{html.escape(a.pillar_name)}</td>
        </tr>
        """)
    actions_table_rows = "".join(actions_html)

    # Simulações
    simulations_html = []
    for sim in report.simulations:
        simulations_html.append(f"""
        <div class="sim-card">
            <div class="sim-title">{html.escape(sim['scenario'])}</div>
            <div class="sim-gain">Ganho: <strong>{html.escape(sim['estimated_gain'])}</strong></div>
            <div class="sim-projected">Novo SSI: <span class="highlight">{html.escape(str(sim['projected_ssi']))} / 100</span></div>
            <div class="sim-focus">Foco: {html.escape(sim['main_impact'])}</div>
        </div>
        """)
    simulations_block = "".join(simulations_html)

    # Montagem do template final HTML
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório LinkedIn SSI - {html.escape(user_name)}</title>
    <style>
        :root {{
            --primary: #0A66C2;
            --primary-dark: #004182;
            --bg-color: #F3F4F6;
            --card-bg: #FFFFFF;
            --text-main: #1F2937;
            --text-muted: #6B7280;
            --border-color: #E5E7EB;
            --success: #10B981;
            --warning: #F59E0B;
            --danger: #EF4444;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 1050px;
            margin: 0 auto;
        }}

        /* Header */
        .header-card {{
            background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
            color: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(10, 102, 194, 0.25);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}

        .user-info h1 {{
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .user-info p.headline {{
            font-size: 15px;
            opacity: 0.9;
            max-width: 650px;
            margin-bottom: 8px;
        }}

        .user-info .ref-date {{
            font-size: 13px;
            opacity: 0.75;
        }}

        .score-box {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 14px;
            padding: 20px 28px;
            text-align: center;
            min-width: 190px;
        }}

        .score-box .score-label {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .score-box .score-number {{
            font-size: 44px;
            font-weight: 800;
            line-height: 1;
        }}

        .score-box .score-max {{
            font-size: 16px;
            opacity: 0.8;
            font-weight: 500;
        }}

        .percentiles-row {{
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }}

        .percentile-card {{
            flex: 1;
            min-width: 250px;
            background: var(--card-bg);
            border-radius: 12px;
            padding: 18px 24px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .percentile-icon {{
            font-size: 28px;
        }}

        .percentile-text strong {{
            display: block;
            font-size: 16px;
            color: var(--primary);
        }}

        .percentile-text span {{
            font-size: 13px;
            color: var(--text-muted);
        }}

        /* Section Titles */
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            margin: 28px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* Pillars Grid */
        .pillars-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
            gap: 20px;
            margin-bottom: 28px;
        }}

        @media (max-width: 600px) {{
            .pillars-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .pillar-card {{
            background: var(--card-bg);
            border-radius: 14px;
            border: 1px solid var(--border-color);
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        .pillar-header {{
            padding: 16px 20px;
            background: #FAFAFA;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .pillar-title-area {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .pillar-icon {{
            font-size: 24px;
        }}

        .pillar-title {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-main);
        }}

        .pillar-subtitle {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .pillar-score-badge {{
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 700;
            font-size: 14px;
        }}

        .pillar-body {{
            padding: 20px;
            flex: 1;
        }}

        .progress-info {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}

        .progress-bar-container {{
            background: #E5E7EB;
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
            margin-bottom: 16px;
        }}

        .progress-bar-container.small {{
            height: 6px;
            margin-bottom: 6px;
        }}

        .progress-bar-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.6s ease;
        }}

        /* Accordion for submetrics */
        .submetrics-accordion summary {{
            font-size: 13px;
            font-weight: 600;
            color: var(--primary);
            cursor: pointer;
            padding: 8px 0;
            user-select: none;
        }}

        .submetrics-list {{
            margin-top: 12px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            border-top: 1px dashed var(--border-color);
            padding-top: 12px;
        }}

        .submetric-item {{
            background: #F9FAFB;
            border: 1px solid #EEF2F6;
            border-radius: 8px;
            padding: 10px 14px;
        }}

        .submetric-header {{
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            margin-bottom: 4px;
        }}

        .submetric-name {{
            font-weight: 600;
        }}

        .submetric-score {{
            color: var(--primary-dark);
        }}

        .submetric-meta {{
            font-size: 12px;
            color: #4B5563;
            margin-top: 4px;
            font-family: Consolas, monospace;
        }}

        .submetric-desc {{
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 4px;
            line-height: 1.3;
        }}

        /* Executive Diagnostic Card */
        .diagnostic-card {{
            background: var(--card-bg);
            border-radius: 14px;
            border: 1px solid var(--border-color);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}

        .headline-diag {{
            font-size: 16px;
            font-weight: 600;
            padding: 14px 18px;
            background: #EFF6FF;
            border-left: 4px solid var(--primary);
            border-radius: 6px;
            margin-bottom: 20px;
            color: #1E40AF;
        }}

        .diag-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        @media (max-width: 768px) {{
            .diag-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .diag-box h4 {{
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .diag-box ul {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .diag-box li {{
            font-size: 13px;
            display: flex;
            align-items: flex-start;
            gap: 8px;
            line-height: 1.4;
        }}

        .icon.check {{ color: var(--success); font-weight: bold; }}
        .icon.warn {{ color: var(--warning); font-weight: bold; }}

        /* Action Plan Table */
        .table-card {{
            background: var(--card-bg);
            border-radius: 14px;
            border: 1px solid var(--border-color);
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
            overflow-x: auto;
        }}

        table.action-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        table.action-table th {{
            text-align: left;
            background: #F9FAFB;
            padding: 12px 14px;
            font-weight: 600;
            color: var(--text-muted);
            border-bottom: 2px solid var(--border-color);
        }}

        table.action-table td {{
            padding: 14px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: top;
        }}

        .prio-tag {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .prio-alta {{ background: #FEE2E2; color: #DC2626; }}
        .prio-media {{ background: #FEF3C7; color: #D97706; }}
        .prio-baixa {{ background: #DBEAFE; color: #2563EB; }}

        .impact-badge {{
            background: #ECFDF5;
            color: #059669;
            font-weight: 600;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 13px;
            display: inline-block;
        }}

        .action-how {{
            font-size: 12px;
            color: #4B5563;
            margin-top: 6px;
        }}

        .action-pillar {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* Simulations Grid */
        .sim-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}

        .sim-card {{
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            padding: 18px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}

        .sim-title {{
            font-weight: 700;
            font-size: 14px;
            margin-bottom: 8px;
            color: var(--primary);
        }}

        .sim-gain {{
            font-size: 13px;
            color: var(--success);
            margin-bottom: 4px;
        }}

        .sim-projected {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 6px;
        }}

        .sim-projected .highlight {{
            color: #D97706;
        }}

        .sim-focus {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        /* Footer & Print */
        .report-footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 36px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
        }}

        .print-btn {{
            background: var(--primary);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 12px;
        }}

        .print-btn:hover {{
            background: var(--primary-dark);
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .print-btn {{
                display: none;
            }}
            .submetrics-accordion details {{
                open: true;
            }}
            .submetrics-list {{
                display: flex !important;
            }}
        }}
    </style>
</head>
<body>

<div class="container">
    <!-- Header -->
    <div class="header-card">
        <div class="user-info">
            <h1>{html.escape(user_name)}</h1>
            <p class="headline">{headline}</p>
            <p class="ref-date">📅 Data de Referência dos Dados: {ref_date_str}</p>
        </div>
        <div class="score-box">
            <div class="score-label">Score SSI Total</div>
            <div class="score-number">{total_score}</div>
            <div class="score-max">de 100 pontos</div>
        </div>
    </div>

    <!-- Percentiles -->
    <div class="percentiles-row">
        <div class="percentile-card">
            <span class="percentile-icon">🏢</span>
            <div class="percentile-text">
                <strong>{html.escape(result.industry_percentile)}</strong>
                <span>Classificação relativa entre profissionais da sua indústria</span>
            </div>
        </div>
        <div class="percentile-card">
            <span class="percentile-icon">🌐</span>
            <div class="percentile-text">
                <strong>{html.escape(result.network_percentile)}</strong>
                <span>Classificação relativa dentro da sua rede de conexões</span>
            </div>
        </div>
    </div>

    <!-- 4 Pillars Section -->
    <h2 class="section-title">📊 Desempenho nos 4 Pilares do SSI</h2>
    <div class="pillars-grid">
        {pillars_section}
    </div>

    <!-- Executive Diagnostic -->
    <h2 class="section-title">🩺 Diagnóstico Estratégico</h2>
    <div class="diagnostic-card">
        <div class="headline-diag">
            {html.escape(report.headline_diagnostic)}
        </div>
        <div class="diag-grid">
            <div class="diag-box">
                <h4 style="color: var(--success);">✅ Pontos Fortes</h4>
                <ul>{strengths_html if strengths_html else "<li>Nenhum ponto forte acima de 18 pts registrado.</li>"}</ul>
            </div>
            <div class="diag-box">
                <h4 style="color: var(--warning);">⚠️ Gargalos de Pontuação</h4>
                <ul>{bottlenecks_html if bottlenecks_html else "<li>Perfil com alto equilíbrio em todos os pilares.</li>"}</ul>
            </div>
        </div>
    </div>

    <!-- Strategic Action Plan -->
    <h2 class="section-title">🎯 Plano de Ação (Ações com Maior Retorno)</h2>
    <div class="table-card">
        <table class="action-table">
            <thead>
                <tr>
                    <th style="width: 110px;">Prioridade</th>
                    <th>Ação Recomendada & Como Fazer</th>
                    <th style="width: 170px;">Impacto Estimado</th>
                    <th style="width: 180px;">Pilar Alvo</th>
                </tr>
            </thead>
            <tbody>
                {actions_table_rows}
            </tbody>
        </table>
    </div>

    <!-- Growth Simulations -->
    <h2 class="section-title">📈 Projeções de Crescimento</h2>
    <div class="sim-grid">
        {simulations_block}
    </div>

    <!-- Footer -->
    <div class="report-footer">
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir ou Salvar em PDF (Ctrl + P)</button>
        <p>Relatório gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} pelo <strong>LinkedIn SSI Calculator (Open-Source)</strong>.</p>
        <p>Processamento 100% local e confidencial em conformidade com LGPD/GDPR. Nenhum dado foi enviado à nuvem.</p>
    </div>
</div>

<script>
    // Abre automaticamente os acordeões se o usuário for imprimir
    window.addEventListener('beforeprint', () => {{
        document.querySelectorAll('details').forEach(el => el.setAttribute('open', ''));
    }});
</script>

</body>
</html>
"""

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.abspath(f"relatorio_ssi_{timestamp}.html")
    else:
        output_path = os.path.abspath(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path

