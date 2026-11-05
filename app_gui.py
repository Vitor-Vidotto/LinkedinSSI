"""
app_gui.py - Interface Gráfica Moderna (GUI) para a Calculadora de LinkedIn SSI.
Permite selecionar o diretório dos dados extraídos do LinkedIn (ou arquivo .zip),
calcular a pontuação dos 4 pilares e gerar relatórios visuais completos em HTML e JSON.
"""

import os
import sys
import json
import threading
import webbrowser
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

# Garante que o diretório atual e 'src' estejam acessíveis
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

def resource_path(relative_path: str) -> str:
    """Retorna o caminho absoluto do recurso, suportando execução local e PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(CURRENT_DIR, relative_path)

import customtkinter as ctk
from src.parser import LinkedInDataParser
from src.metrics import MetricsExtractor
from src.ssi_engine import SSIEngine, SSIResult
from src.recommendations import RecommendationsGenerator, DiagnosticReport
from src.report_generator import generate_html_report

# Configuração visual do CustomTkinter
ctk.set_appearance_mode("Dark")  # "Dark", "Light", "System"
ctk.set_default_color_theme("blue")  # Tema azul similar ao LinkedIn


class LinkedInSSIGui(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Calculadora de LinkedIn SSI (Social Selling Index)")
        self.geometry("900x740")
        self.minsize(800, 650)

        # Configura ícone da janela
        icon_file = resource_path("app_icon.ico")
        if os.path.exists(icon_file):
            try:
                self.iconbitmap(icon_file)
            except Exception:
                pass

        # Estado da aplicação
        self.selected_path: str = ""
        self.current_result: Optional[SSIResult] = None
        self.current_report: Optional[DiagnosticReport] = None
        self.generated_html_path: Optional[str] = None

        self._build_ui()
        self._auto_detect_initial_path()

    def _build_ui(self):
        # Container principal com scroll para comportar todas as resoluções
        self.main_scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.main_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # 1. Cabeçalho / Hero
        self.header_frame = ctk.CTkFrame(self.main_scroll, fg_color=("#0A66C2", "#004182"), corner_radius=12)
        self.header_frame.pack(fill="x", padx=20, pady=(15, 15))

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text="📊 Calculadora Open-Source de LinkedIn SSI",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        )
        self.lbl_title.pack(anchor="w", padx=20, pady=(15, 4))

        self.lbl_subtitle = ctk.CTkLabel(
            self.header_frame,
            text="Estime seu Social Selling Index gratuitamente a partir da exportação oficial de dados do LinkedIn (100% offline e privado).",
            font=ctk.CTkFont(size=13),
            text_color="#E0E7FF",
            wraplength=760,
            justify="left"
        )
        self.lbl_subtitle.pack(anchor="w", padx=20, pady=(0, 15))

        # 2. Seção de Seleção de Diretório / Arquivo
        self.file_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12)
        self.file_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_input_title = ctk.CTkLabel(
            self.file_frame,
            text="📁 Selecione o Diretório dos Dados Extraídos:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_input_title.pack(anchor="w", padx=20, pady=(15, 5))

        self.lbl_input_desc = ctk.CTkLabel(
            self.file_frame,
            text="Escolha a pasta onde você descompactou o arquivo do LinkedIn (ou selecione diretamente o arquivo .zip original):",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_input_desc.pack(anchor="w", padx=20, pady=(0, 10))

        # Linha de entrada de caminho e botões de procura
        self.path_entry_row = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        self.path_entry_row.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_path = ctk.CTkEntry(
            self.path_entry_row,
            placeholder_text="Caminho para a pasta descompactada (ex: C:\\MeusDados\\Descompilado)...",
            height=38,
            font=ctk.CTkFont(size=13)
        )
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_browse_folder = ctk.CTkButton(
            self.path_entry_row,
            text="📂 Escolher Pasta...",
            command=self._on_browse_folder,
            width=140,
            height=38,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.btn_browse_folder.pack(side="left", padx=(0, 5))

        self.btn_browse_zip = ctk.CTkButton(
            self.path_entry_row,
            text="📦 Ou Arquivo .ZIP...",
            command=self._on_browse_zip,
            width=140,
            height=38,
            fg_color="#374151",
            hover_color="#4B5563",
            font=ctk.CTkFont(size=12)
        )
        self.btn_browse_zip.pack(side="left")

        # Opção de abrir automaticamente o relatório
        self.auto_open_var = ctk.BooleanVar(value=True)
        self.chk_auto_open = ctk.CTkCheckBox(
            self.file_frame,
            text="Gerar e abrir relatório HTML automaticamente no navegador após o cálculo",
            variable=self.auto_open_var,
            font=ctk.CTkFont(size=12)
        )
        self.chk_auto_open.pack(anchor="w", padx=20, pady=(0, 15))

        # Botão de Ação Principal
        self.btn_calculate = ctk.CTkButton(
            self.file_frame,
            text="🚀 CALCULAR LINKEDIN SSI E GERAR RELATÓRIO",
            command=self._on_start_calculation,
            height=46,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#0A66C2",
            hover_color="#004182"
        )
        self.btn_calculate.pack(fill="x", padx=20, pady=(0, 20))

        # Barra de Progresso e Status
        self.status_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_status = ctk.CTkLabel(
            self.status_frame,
            text="Pronto para analisar. Selecione a pasta acima e clique em 'Calcular'.",
            font=ctk.CTkFont(size=12),
            text_color="#9CA3AF"
        )
        self.lbl_status.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, mode="indeterminate")
        # Será mostrada durante o processamento

        # 3. Painel de Resultados (Oculto inicialmente)
        self.results_frame = ctk.CTkFrame(self.main_scroll, corner_radius=12)
        # Não empacotado até que haja resultado

    def _auto_detect_initial_path(self):
        """Tenta encontrar automaticamente pastas ou zips comuns no diretório atual."""
        candidates = [
            os.path.join(CURRENT_DIR, "Dados", "Descompilado"),
            os.path.join(CURRENT_DIR, "Descompilado"),
            os.path.join(CURRENT_DIR, "data"),
            os.path.join(CURRENT_DIR, "dados")
        ]
        for cd in candidates:
            if os.path.isdir(cd):
                self.entry_path.delete(0, "end")
                self.entry_path.insert(0, os.path.abspath(cd))
                return

        # Verifica zips
        search_dirs = [os.path.join(CURRENT_DIR, "Dados"), CURRENT_DIR]
        for sd in search_dirs:
            if os.path.isdir(sd):
                for f in os.listdir(sd):
                    if f.lower().endswith(".zip") and "linkedin" in f.lower():
                        self.entry_path.delete(0, "end")
                        self.entry_path.insert(0, os.path.abspath(os.path.join(sd, f)))
                        return

    def _on_browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a Pasta dos Dados Extraídos do LinkedIn")
        if folder:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, os.path.abspath(folder))

    def _on_browse_zip(self):
        zip_file = filedialog.askopenfilename(
            title="Selecione o Arquivo .ZIP do LinkedIn",
            filetypes=[("Arquivos ZIP", "*.zip"), ("Todos os Arquivos", "*.*")]
        )
        if zip_file:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, os.path.abspath(zip_file))

    def _set_ui_processing(self, is_processing: bool, message: str = ""):
        if is_processing:
            self.btn_calculate.configure(state="disabled", text="⏳ Processando dados do LinkedIn...")
            self.btn_browse_folder.configure(state="disabled")
            self.btn_browse_zip.configure(state="disabled")
            self.lbl_status.configure(text=message or "Lendo arquivos CSV e extraindo métricas...")
            self.progress_bar.pack(fill="x", pady=(5, 0))
            self.progress_bar.start()
        else:
            self.btn_calculate.configure(state="normal", text="🚀 CALCULAR LINKEDIN SSI E GERAR RELATÓRIO")
            self.btn_browse_folder.configure(state="normal")
            self.btn_browse_zip.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
            if message:
                self.lbl_status.configure(text=message)

    def _on_start_calculation(self):
        path = self.entry_path.get().strip()
        if not path:
            messagebox.showwarning("Caminho não informado", "Por favor, selecione o diretório dos dados ou arquivo .zip.")
            return

        if not os.path.exists(path):
            messagebox.showerror("Caminho Inválido", f"O diretório ou arquivo especificado não existe:\n{path}")
            return

        self.selected_path = path
        self._set_ui_processing(True, f"Analisando dados de '{os.path.basename(path)}'...")

        # Executa em thread separada para não congelar a interface gráfica
        threading.Thread(target=self._run_calculation_thread, daemon=True).start()

    def _run_calculation_thread(self):
        try:
            parser_obj = LinkedInDataParser(self.selected_path)
            extractor = MetricsExtractor(parser_obj)
            metrics = extractor.extract()
            engine = SSIEngine()
            result = engine.calculate(metrics)
            rec_gen = RecommendationsGenerator()
            report = rec_gen.generate(result)
            parser_obj.close()

            # Gera relatório HTML
            user_clean = f"{metrics.first_name}_{metrics.last_name}".strip() or "usuario"
            user_clean = "".join(c for c in user_clean if c.isalnum() or c in ("_", "-"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"relatorio_ssi_{user_clean}_{timestamp}.html"
            
            # Se for diretório, salva ao lado ou no diretório de dados
            if os.path.isdir(self.selected_path):
                out_dir = self.selected_path
            else:
                out_dir = os.path.dirname(self.selected_path) or CURRENT_DIR
                
            report_path = os.path.join(out_dir, report_name)
            generated_html = generate_html_report(result, report, report_path)

            # Notifica na thread principal do Tkinter
            self.after(0, lambda: self._on_calculation_success(result, report, generated_html))

        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self._on_calculation_error(err_msg))

    def _on_calculation_error(self, error_message: str):
        self._set_ui_processing(False, f"❌ Erro ao calcular: {error_message}")
        messagebox.showerror(
            "Erro no Processamento",
            f"Ocorreu um erro ao processar os arquivos do LinkedIn:\n\n{error_message}\n\nVerifique se o diretório selecionado contém os arquivos CSV oficiais da exportação."
        )

    def _on_calculation_success(self, result: SSIResult, report: DiagnosticReport, html_path: str):
        self.current_result = result
        self.current_report = report
        self.generated_html_path = html_path

        msg = f"✅ Cálculo concluído com sucesso! Relatório gerado em: {os.path.basename(html_path)}"
        self._set_ui_processing(False, msg)

        # Renderiza os resultados no painel visual
        self._render_results_panel(result, report, html_path)

        # Abre no navegador se a caixa de seleção estiver ativa
        if self.auto_open_var.get():
            try:
                webbrowser.open(f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}")
            except Exception:
                pass

    def _render_results_panel(self, result: SSIResult, report: DiagnosticReport, html_path: str):
        # Limpa o frame se já tiver sido desenhado antes
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        self.results_frame.pack(fill="x", padx=20, pady=(10, 25))

        m = result.metrics
        user_name = f"{m.first_name} {m.last_name}".strip() or "Profissional"

        # 1. Top Card do Score Consolidado
        total_color = "#10B981" if result.total_score >= 70 else ("#0A66C2" if result.total_score >= 50 else ("#F59E0B" if result.total_score >= 40 else "#EF4444"))
        
        score_card = ctk.CTkFrame(self.results_frame, fg_color=("#1E293B", "#0F172A"), corner_radius=10)
        score_card.pack(fill="x", padx=15, pady=(15, 10))

        score_inner = ctk.CTkFrame(score_card, fg_color="transparent")
        score_inner.pack(fill="x", padx=20, pady=15)

        # Lado esquerdo: Nome e Percentis
        left_info = ctk.CTkFrame(score_inner, fg_color="transparent")
        left_info.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left_info,
            text=f"👤 {user_name}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w")

        if m.headline:
            ctk.CTkLabel(
                left_info,
                text=m.headline[:80] + ("..." if len(m.headline) > 80 else ""),
                font=ctk.CTkFont(size=12),
                text_color="#94A3B8"
            ).pack(anchor="w", pady=(2, 6))

        ctk.CTkLabel(
            left_info,
            text=f"🏢 {result.industry_percentile}   |   🌐 {result.network_percentile}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38BDF8"
        ).pack(anchor="w")

        # Lado direito: Grande Score Total
        right_score = ctk.CTkFrame(score_inner, fg_color="transparent")
        right_score.pack(side="right", padx=(10, 0))

        ctk.CTkLabel(
            right_score,
            text="SCORE SSI TOTAL",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8"
        ).pack(anchor="e")

        ctk.CTkLabel(
            right_score,
            text=f"{result.total_score:.2f}",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=total_color
        ).pack(anchor="e")

        ctk.CTkLabel(
            right_score,
            text="de 100 pontos",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8"
        ).pack(anchor="e")

        # 2. Desempenho dos 4 Pilares
        ctk.CTkLabel(
            self.results_frame,
            text="Desempenho nos 4 Pilares:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(10, 5))

        pillars_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        pillars_frame.pack(fill="x", padx=15, pady=(0, 15))

        pillars = [result.pillar_1, result.pillar_2, result.pillar_3, result.pillar_4]
        for p in pillars:
            p_card = ctk.CTkFrame(pillars_frame, corner_radius=8)
            p_card.pack(fill="x", pady=4)

            row = ctk.CTkFrame(p_card, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=8)

            # Nome e Score
            name_lbl = ctk.CTkLabel(
                row,
                text=f"P{p.pillar_id}: {p.name}",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
                width=280
            )
            name_lbl.pack(side="left")

            # Barra de progresso
            pct = min(1.0, max(0.0, p.score / 25.0))
            pbar = ctk.CTkProgressBar(row, width=180, height=10, progress_color=p.color)
            pbar.set(pct)
            pbar.pack(side="left", padx=15)

            score_lbl = ctk.CTkLabel(
                row,
                text=f"{p.score:.2f} / 25.00  ({p.level})",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=p.color,
                width=160,
                anchor="e"
            )
            score_lbl.pack(side="right")

        # 3. Botões de Relatório e Exportação
        btn_action_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        btn_action_row.pack(fill="x", padx=15, pady=(10, 20))

        btn_open_html = ctk.CTkButton(
            btn_action_row,
            text="📄 Abrir Relatório Completo (HTML)",
            command=self._on_open_html,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        btn_open_html.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_save_as = ctk.CTkButton(
            btn_action_row,
            text="💾 Salvar Relatório em Outro Local...",
            command=self._on_save_html_as,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4B5563"
        )
        btn_save_as.pack(side="left", fill="x", expand=True, padx=(0, 8))

        btn_export_json = ctk.CTkButton(
            btn_action_row,
            text="💾 Exportar JSON",
            command=self._on_export_json,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#374151",
            hover_color="#4B5563"
        )
        btn_export_json.pack(side="left", fill="x", expand=True)

    def _on_open_html(self):
        if self.generated_html_path and os.path.exists(self.generated_html_path):
            webbrowser.open(f"file:///{os.path.abspath(self.generated_html_path).replace(os.sep, '/')}")
        else:
            messagebox.showwarning("Relatório Não Encontrado", "O arquivo do relatório não foi localizado.")

    def _on_save_html_as(self):
        if not self.current_result or not self.current_report:
            return

        target_file = filedialog.asksaveasfilename(
            title="Salvar Relatório HTML Como",
            defaultextension=".html",
            filetypes=[("Página HTML", "*.html"), ("Todos os Arquivos", "*.*")],
            initialfile=os.path.basename(self.generated_html_path) if self.generated_html_path else "relatorio_ssi.html"
        )
        if target_file:
            try:
                generate_html_report(self.current_result, self.current_report, target_file)
                messagebox.showinfo("Sucesso", f"Relatório salvo com sucesso em:\n{target_file}")
            except Exception as e:
                messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}")

    def _on_export_json(self):
        if not self.current_result or not self.current_report:
            return

        target_file = filedialog.asksaveasfilename(
            title="Exportar Dados em JSON",
            defaultextension=".json",
            filetypes=[("Arquivo JSON", "*.json"), ("Todos os Arquivos", "*.*")],
            initialfile="ssi_report.json"
        )
        if target_file:
            try:
                payload = {
                    "metadata": {
                        "generated_at": datetime.now().isoformat(),
                        "source": os.path.abspath(self.selected_path)
                    },
                    "ssi_result": self.current_result.to_dict(),
                    "diagnostic_report": self.current_report.to_dict()
                }
                with open(target_file, "w", encoding="utf-8") as fp:
                    json.dump(payload, fp, indent=2, ensure_ascii=False)
                messagebox.showinfo("Sucesso", f"JSON exportado com sucesso em:\n{target_file}")
            except Exception as e:
                messagebox.showerror("Erro ao Exportar", f"Não foi possível exportar o JSON:\n{e}")


def main():
    app = LinkedInSSIGui()
    app.mainloop()


if __name__ == "__main__":
    main()
