"""
cli.py - Interface de Linha de Comando (CLI) para a Calculadora de LinkedIn SSI.
Suporta visualização rica com cores, barras de progresso, diagnósticos e exportação JSON.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Garante que 'src' esteja no PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Corrige encoding no terminal do Windows para suportar emojis e caracteres acentuados
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.parser import LinkedInDataParser
from src.metrics import MetricsExtractor
from src.ssi_engine import SSIEngine, SSIResult
from src.recommendations import RecommendationsGenerator, DiagnosticReport
from src.report_generator import generate_html_report

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.progress_bar import ProgressBar
    from rich.layout import Layout
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def render_ascii_bar(score: float, max_score: float = 25.0, width: int = 20) -> str:
    """Gera uma barra de progresso visual em texto puro."""
    pct = min(1.0, max(0.0, score / max_score))
    filled = int(round(pct * width))
    empty = width - filled
    return f"[{'█' * filled}{'░' * empty}] {pct*100:5.1f}%"


def print_rich_report(console: "Console", result: SSIResult, report: DiagnosticReport, verbose: bool = False):
    """Renderiza relatório visual de alta fidelidade usando a biblioteca Rich."""
    m = result.metrics

    # Cabeçalho Principal
    header_text = Text()
    header_text.append("📊 CALCULADORA OPEN-SOURCE DE LINKEDIN SSI\n", style="bold cyan")
    header_text.append("Estimativa do Social Selling Index a partir do pacote oficial de dados do LinkedIn", style="italic white")
    console.print(Panel(header_text, box=box.ROUNDED, border_style="cyan"))

    # Painel do Usuário
    user_info = Table.grid(padding=(0, 2))
    user_info.add_column(style="bold white")
    user_info.add_column(style="yellow")
    user_info.add_column(style="bold white")
    user_info.add_column(style="green")

    user_info.add_row(
        "👤 Profissional:", f"{m.first_name} {m.last_name}".strip() or "Usuário LinkedIn",
        "📅 Data Ref. da Exportação:", m.reference_date.strftime("%d/%m/%Y %H:%M UTC")
    )
    if m.headline:
        user_info.add_row("💼 Título / Headline:", m.headline[:75] + ("..." if len(m.headline) > 75 else ""), "", "")

    console.print(Panel(user_info, title="[bold]Dados do Titular[/bold]", border_style="bright_blue", box=box.ROUNDED))

    # Painel do Score Total
    total_color = "green" if result.total_score >= 70 else ("cyan" if result.total_score >= 50 else ("yellow" if result.total_score >= 40 else "red"))
    score_panel_text = Text()
    score_panel_text.append(f"\n  SCORE SSI TOTAL: {result.total_score:.2f} / 100\n", style=f"bold {total_color}")
    score_panel_text.append(f"  • Posição Estimada no Setor: {result.industry_percentile}\n", style="white")
    score_panel_text.append(f"  • Posição Estimada na sua Rede: {result.network_percentile}\n", style="white")
    console.print(Panel(score_panel_text, title="[bold]Pontuação Consolidada[/bold]", border_style=total_color, box=box.HEAVY))

    # Tabela dos 4 Pilares
    table = Table(title="Desempenho nos 4 Pilares do Social Selling Index", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("Pilar", style="bold white", width=36)
    table.add_column("Pontos", justify="right", style="bold", width=12)
    table.add_column("Progresso", justify="center", width=26)
    table.add_column("Classificação", justify="center", width=18)

    pillars = [
        result.pillar_1,
        result.pillar_2,
        result.pillar_3,
        result.pillar_4
    ]

    pillar_styles = {
        1: "bright_yellow",
        2: "bright_green",
        3: "bright_blue",
        4: "bright_magenta"
    }

    for p in pillars:
        st = pillar_styles.get(p.pillar_id, "white")
        bar = render_ascii_bar(p.score, 25.0, width=15)
        
        level_style = "green" if p.level == "Excelente" else ("cyan" if p.level == "Bom" else ("yellow" if p.level == "Moderado" else "red"))
        table.add_row(
            f"[{st}]P{p.pillar_id}: {p.name}[/{st}]",
            f"[{st}]{p.score:.2f} / 25.00[/{st}]",
            f"[{st}]{bar}[/{st}]",
            f"[{level_style}]{p.level}[/{level_style}]"
        )

    console.print(table)

    # Detalhamento de Submétricas (se verbose for ativado)
    if verbose:
        console.print("\n")
        det_table = Table(title="Detalhamento das Submétricas e Fórmulas por Pilar", box=box.SIMPLE_HEAVY)
        det_table.add_column("Pilar / Submétrica", style="bold cyan", width=35)
        det_table.add_column("Pts", justify="right", style="bold green", width=10)
        det_table.add_column("Dado Bruto Extraído", style="white", width=42)
        det_table.add_column("Explicação do Algoritmo", style="italic dim white")

        for p in pillars:
            st = pillar_styles.get(p.pillar_id, "white")
            det_table.add_row(f"[{st}]P{p.pillar_id}: {p.name} ({p.score:.2f} pts)[/{st}]", "", "", "")
            for s in p.submetrics:
                det_table.add_row(
                    f"  ↳ {s.name}",
                    f"{s.score:.2f}/{s.max_score:.1f}",
                    str(s.raw_value),
                    s.description
                )
        console.print(det_table)

    # Diagnóstico e Plano de Ação
    diag_text = Text()
    diag_text.append(f"{report.headline_diagnostic}\n\n", style="bold white")

    diag_text.append("✅ PONTOS FORTES IDENTIFICADOS:\n", style="bold green")
    for st in report.strengths:
        diag_text.append(f"  • {st}\n", style="green")

    if report.bottlenecks:
        diag_text.append("\n⚠️ PRINCIPAIS GARGALOS (ONDE VOCÊ PERDE PONTOS):\n", style="bold yellow")
        for bn in report.bottlenecks:
            diag_text.append(f"  • {bn}\n", style="yellow")

    console.print(Panel(diag_text, title="[bold]Diagnóstico Executivo[/bold]", border_style="yellow", box=box.ROUNDED))

    # Ações Recomendadas
    act_table = Table(title="🎯 Plano de Ação Estratégico (Maior Retorno de SSI)", box=box.ROUNDED)
    act_table.add_column("Prioridade", justify="center", width=12)
    act_table.add_column("Ação Recomendada", style="bold white", width=38)
    act_table.add_column("Impacto Estimado", style="bold green", width=22)
    act_table.add_column("Como Executar", style="italic white")

    for act in report.actions:
        prio_color = "red" if act.priority == "Alta" else ("yellow" if act.priority == "Média" else "blue")
        act_table.add_row(
            f"[{prio_color}]{act.priority}[/{prio_color}]",
            act.title,
            act.impact_estimate,
            act.how_to_do
        )

    console.print(act_table)

    # Simulações de Crescimento
    sim_table = Table(title="📈 Projeções de Crescimento de SSI", box=box.ROUNDED)
    sim_table.add_column("Cenário de Ativação", style="bold cyan", width=40)
    sim_table.add_column("Ganho Estimado", style="bold green", justify="center", width=18)
    sim_table.add_column("Novo SSI Projetado", style="bold yellow", justify="center", width=20)
    sim_table.add_column("Foco de Alavancagem", style="white")

    for sim in report.simulations:
        sim_table.add_row(
            sim["scenario"],
            sim["estimated_gain"],
            f"{sim['projected_ssi']} / 100",
            sim["main_impact"]
        )

    console.print(sim_table)


def print_plain_report(result: SSIResult, report: DiagnosticReport, verbose: bool = False):
    """Renderização em texto puro caso Rich não esteja instalado."""
    print("=" * 70)
    print("  CALCULADORA DE LINKEDIN SSI (SOCIAL SELLING INDEX)")
    print("=" * 70)
    m = result.metrics
    print(f"Usuário: {m.first_name} {m.last_name}")
    print(f"Data de Referência: {m.reference_date.strftime('%d/%m/%Y %H:%M UTC')}")
    print(f"\nSCORE SSI TOTAL: {result.total_score:.2f} / 100.00")
    print(f"Classificação no Setor: {result.industry_percentile}")
    print(f"Classificação na Rede:  {result.network_percentile}")
    print("-" * 70)
    print("PONTUAÇÃO DOS 4 PILARES:")
    for p in [result.pillar_1, result.pillar_2, result.pillar_3, result.pillar_4]:
        bar = render_ascii_bar(p.score, 25.0, width=15)
        print(f"  P{p.pillar_id} - {p.name:<32}: {p.score:5.2f}/25.00 {bar} ({p.level})")

    print("\n" + "=" * 70)
    print("DIAGNÓSTICO E RECOMENDAÇÕES:")
    print(report.headline_diagnostic)
    print("\nAÇÕES PRIORITÁRIAS:")
    for a in report.actions:
        print(f"  [{a.priority}] {a.title} ({a.impact_estimate})")
        print(f"    -> Como fazer: {a.how_to_do}\n")


def auto_detect_source() -> str:
    """Busca automaticamente pela pasta de dados ou arquivo ZIP no diretório atual."""
    # 1. Pasta Dados/Descompilado
    candidate_dirs = [
        os.path.join("Dados", "Descompilado"),
        "Descompilado",
        "data",
        "dados"
    ]
    for cd in candidate_dirs:
        if os.path.isdir(cd):
            return cd

    # 2. Arquivos .zip na pasta Dados ou raiz
    search_dirs = [os.path.join(".", "Dados"), "."]
    for sd in search_dirs:
        if os.path.isdir(sd):
            for f in os.listdir(sd):
                if f.lower().endswith(".zip") and "linkedin" in f.lower():
                    return os.path.join(sd, f)
            for f in os.listdir(sd):
                if f.lower().endswith(".zip"):
                    return os.path.join(sd, f)

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Calculadora de LinkedIn SSI - Processa exportações oficiais do LinkedIn e estima seu Social Selling Index.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Caminho para a pasta descompactada dos dados ou para o arquivo .zip da exportação."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Exibe o detalhamento completo de todas as submétricas e fórmulas."
    )
    parser.add_argument(
        "--export-json",
        metavar="ARQUIVO.json",
        help="Salva todo o diagnóstico e métricas em um arquivo JSON estruturado."
    )
    parser.add_argument(
        "--export-html",
        metavar="ARQUIVO.html",
        help="Gera e salva o relatório visual completo em página HTML (imprimível em PDF)."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Inicia a interface gráfica visual interativa."
    )
    parser.add_argument(
        "--no-rich",
        action="store_true",
        help="Desativa a formatação colorida do Rich e imprime em texto padrão."
    )

    args = parser.parse_args()

    if args.gui:
        from app_gui import main as run_gui
        run_gui()
        return

    # Determina o caminho da fonte de dados
    source_path = args.source
    if not source_path:
        source_path = auto_detect_source()
        if not source_path:
            print("❌ Erro: Nenhuma pasta ou arquivo .zip do LinkedIn foi fornecido ou encontrado automaticamente.")
            print("Uso: python cli.py <caminho_para_pasta_ou_zip>")
            sys.exit(1)

    if not os.path.exists(source_path):
        print(f"❌ Erro: O caminho especificado não existe: {source_path}")
        sys.exit(1)

    # Inicialização do Console
    console = Console(force_terminal=True, legacy_windows=False) if (RICH_AVAILABLE and not args.no_rich) else None

    if console:
        with console.status(f"[bold green]Carregando e analisando dados de '{source_path}'..."):
            parser_obj = LinkedInDataParser(source_path)
            extractor = MetricsExtractor(parser_obj)
            metrics = extractor.extract()
            engine = SSIEngine()
            result = engine.calculate(metrics)
            rec_gen = RecommendationsGenerator()
            report = rec_gen.generate(result)
            parser_obj.close()
    else:
        print(f"Lendo dados de: {source_path}...")
        parser_obj = LinkedInDataParser(source_path)
        extractor = MetricsExtractor(parser_obj)
        metrics = extractor.extract()
        engine = SSIEngine()
        result = engine.calculate(metrics)
        rec_gen = RecommendationsGenerator()
        report = rec_gen.generate(result)
        parser_obj.close()

    # Renderiza o relatório
    if console:
        print_rich_report(console, result, report, verbose=args.verbose)
    else:
        print_plain_report(result, report, verbose=args.verbose)

    # Exportação HTML
    if args.export_html:
        html_out_path = generate_html_report(result, report, args.export_html)
        msg_html = f"\n📄 Relatório HTML gerado com sucesso em: {html_out_path}"
        if console:
            console.print(f"[bold green]{msg_html}[/bold green]")
        else:
            print(msg_html)

    # Exportação JSON
    if args.export_json:
        export_payload = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": os.path.abspath(source_path)
            },
            "ssi_result": result.to_dict(),
            "diagnostic_report": report.to_dict()
        }
        with open(args.export_json, "w", encoding="utf-8") as fp:
            json.dump(export_payload, fp, indent=2, ensure_ascii=False)
        msg = f"\n💾 Relatório completo exportado com sucesso para: {args.export_json}"
        if console:
            console.print(f"[bold green]{msg}[/bold green]")
        else:
            print(msg)


if __name__ == "__main__":
    main()
