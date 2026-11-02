"""
recommendations.py - Gerador de Diagnósticos, Plano de Ação e Simulações de Crescimento.
Analisa os 4 pilares e os dados brutos para sugerir melhorias de maior retorno (ROI).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from .ssi_engine import SSIResult

@dataclass
class ActionItem:
    pillar_id: int
    pillar_name: str
    priority: str  # 'Alta', 'Média', 'Baixa'
    title: str
    impact_estimate: str
    rationale: str
    how_to_do: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pillar_id": self.pillar_id,
            "pillar_name": self.pillar_name,
            "priority": self.priority,
            "title": self.title,
            "impact_estimate": self.impact_estimate,
            "rationale": self.rationale,
            "how_to_do": self.how_to_do
        }

@dataclass
class DiagnosticReport:
    headline_diagnostic: str
    strengths: List[str]
    bottlenecks: List[str]
    actions: List[ActionItem]
    simulations: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline_diagnostic": self.headline_diagnostic,
            "strengths": self.strengths,
            "bottlenecks": self.bottlenecks,
            "actions": [a.to_dict() for a in self.actions],
            "simulations": self.simulations
        }


class RecommendationsGenerator:
    """Analisa o resultado do SSI e gera recomendações práticas."""

    def generate(self, result: SSIResult) -> DiagnosticReport:
        m = result.metrics
        strengths = []
        bottlenecks = []
        actions = []
        simulations = []

        # 1. Análise P1: Marca Profissional
        p1 = result.pillar_1
        if p1.score >= 18:
            strengths.append(f"Marca Profissional Forte ({p1.score:.1f}/25): Perfil muito bem estruturado e completo.")
        else:
            bottlenecks.append(f"Marca Profissional ({p1.score:.1f}/25): Falta de consistência em publicações de conteúdo próprio no feed.")

        if m.shares_90d < 12:
            actions.append(ActionItem(
                pillar_id=1,
                pillar_name=p1.name,
                priority="Alta" if m.shares_90d < 6 else "Média",
                title="Cadência de Publicações Autorais (2x por semana)",
                impact_estimate="+4 a +6 pontos no Pilar 1",
                rationale=f"Você publicou {m.shares_90d} posts nos últimos 90 dias (~1 post a cada {(90/(m.shares_90d or 1)):.0f} dias). O LinkedIn valoriza constância semanal.",
                how_to_do="Compartilhe aprendizados semanais sobre seus projetos de Engenharia de Dados/IA, cases técnicos ou lições aprendidas."
            ))

        # 2. Análise P2: Localizar as Pessoas Certas
        p2 = result.pillar_2
        if p2.score >= 18:
            strengths.append(f"Prospecção Ativa ({p2.score:.1f}/25): Excelente volume de pesquisas e expansão deliberada da rede.")
        else:
            bottlenecks.append(f"Localizar Pessoas Certas ({p2.score:.1f}/25): Oportunidade de refinar filtros de pesquisa para decisores.")

        if m.invitations_sent_90d < 50:
            actions.append(ActionItem(
                pillar_id=2,
                pillar_name=p2.name,
                priority="Média",
                title="Expansão Direcionada com Convites Personalizados",
                impact_estimate="+3 a +5 pontos no Pilar 2",
                rationale="O envio regular de convites para contatos de 2º grau do seu nicho demonstra busca ativa por novos interlocutores.",
                how_to_do="Envie convites sempre acompanhados de uma nota contextualizada mencionando pontos em comum."
            ))

        # 3. Análise P3: Interagir com Insights
        p3 = result.pillar_3
        if p3.score >= 18:
            strengths.append(f"Engajamento Exemplar ({p3.score:.1f}/25): Alta participação nos conteúdos do setor.")
        else:
            bottlenecks.append(f"Interação e Insights ({p3.score:.1f}/25): Menor frequência de comentários e debates no feed.")

        if m.comments_90d < 30:
            actions.append(ActionItem(
                pillar_id=3,
                pillar_name=p3.name,
                priority="Alta",
                title="Comentários Construtivos em Posts Estratégicos (3x por semana)",
                impact_estimate="+5 a +8 pontos no Pilar 3",
                rationale=f"Você fez {m.comments_90d} comentários em 90 dias ({m.comments_30d} no último mês). No algoritmo do LinkedIn, comentários valem até 5x mais do que curtidas simples.",
                how_to_do="Reserve 10 minutos diários para comentar com valor agregado em posts de líderes e colegas da área de dados."
            ))

        if m.reactions_90d < 100:
            actions.append(ActionItem(
                pillar_id=3,
                pillar_name=p3.name,
                priority="Baixa",
                title="Aumentar Reações Diversificadas",
                impact_estimate="+2 a +3 pontos no Pilar 3",
                rationale=f"Você reagiu {m.reactions_90d} vezes em 90 dias. Use reações mais expressivas além de 'LIKE' (como 'APOIO', 'GENIAL', 'PARABÉNS').",
                how_to_do="Interaja com os posts do feed distribuindo reações contextualizadas para movimentar sua presença na rede."
            ))

        # 4. Análise P4: Cultivar Relacionamentos
        p4 = result.pillar_4
        if m.connections_total >= 500:
            strengths.append(f"Rede de Alto Alcance: {m.connections_total:,} conexões diretas (muito acima do teto de 500 conexões do LinkedIn).".replace(",", "."))
        
        if m.decision_maker_ratio < 20.0:
            actions.append(ActionItem(
                pillar_id=4,
                pillar_name=p4.name,
                priority="Média",
                title="Conectar com Líderes e Tomadores de Decisão",
                impact_estimate="+3 a +4 pontos no Pilar 4",
                rationale=f"Atualmente, {m.decision_maker_ratio}% das suas conexões têm cargos como Diretor, VP, Gerente ou Head. Elevar para >20% melhora o perfil relacional.",
                how_to_do="Pesquise por 'Head of Data', 'Data Director', 'CTO' e conecte-se com foco em trocar ideias sobre desafios da indústria."
            ))

        if m.message_threads_90d < 40:
            actions.append(ActionItem(
                pillar_id=4,
                pillar_name=p4.name,
                priority="Média",
                title="Manter Conversas Ativas por Mensagem Direta",
                impact_estimate="+3 a +5 pontos no Pilar 4",
                rationale="O LinkedIn mede se suas conexões geram diálogos reais ou se são apenas números na lista.",
                how_to_do="Ao aceitar conexões ou receber parabenizações, inicie diálogos breves no chat privado."
            ))

        # Simulações de Crescimento
        simulations.append({
            "scenario": "Cenário Consistência (+2 posts/mês, +3 comentários/semana)",
            "estimated_gain": "+8 a +12 pontos",
            "projected_ssi": f"{min(100.0, result.total_score + 10):.1f}",
            "main_impact": "Pilares 1 e 3"
        })
        simulations.append({
            "scenario": "Cenário Aceleração (+1 post autoral/semana, +5 comentários/semana, +10 conversas DM/mês)",
            "estimated_gain": "+15 a +22 pontos",
            "projected_ssi": f"{min(100.0, result.total_score + 18):.1f}",
            "main_impact": "Todos os 4 pilares"
        })

        # Headline
        if result.total_score >= 70:
            hl = f"Excelente índice de Social Selling ({result.total_score:.1f}/100)! Você está entre os perfis mais ativos e influentes do LinkedIn."
        elif result.total_score >= 50:
            hl = f"Bom nível de engajamento ({result.total_score:.1f}/100). Pequenos ajustes de frequência de interação podem alavancar seu SSI para o topo 10%."
        else:
            hl = f"Índice SSI atual em {result.total_score:.1f}/100. Sua base é sólida, mas há um enorme potencial de crescimento aumentando a cadência semanal de interações e postagens."

        return DiagnosticReport(
            headline_diagnostic=hl,
            strengths=strengths,
            bottlenecks=bottlenecks,
            actions=actions,
            simulations=simulations
        )
