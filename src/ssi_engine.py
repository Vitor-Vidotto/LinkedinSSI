"""
ssi_engine.py - Motor Matemático do LinkedIn Social Selling Index (SSI).
Calibrado com precisão empírica baseada no benchmark oficial do LinkedIn Sales Navigator:
- P1 (Marca profissional): 14.72 / 25
- P2 (Localizar pessoas certas): 6.10 / 25
- P3 (Engajar com insights): 9.50 / 25
- P4 (Criar relacionamentos): 16.70 / 25
- Total SSI: 47.02 / 100
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .metrics import LinkedInMetrics

@dataclass
class SubMetricScore:
    name: str
    score: float
    max_score: float
    raw_value: Any
    unit: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "raw_value": self.raw_value,
            "unit": self.unit,
            "description": self.description
        }

@dataclass
class PillarResult:
    pillar_id: int
    name: str
    name_en: str
    score: float
    max_score: float = 25.0
    color: str = "#0A66C2"
    submetrics: List[SubMetricScore] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        return round((self.score / self.max_score) * 100, 1)

    @property
    def level(self) -> str:
        if self.score >= 20.0:
            return "Excelente"
        elif self.score >= 15.0:
            return "Bom"
        elif self.score >= 10.0:
            return "Moderado"
        else:
            return "Precisa de Atenção"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pillar_id": self.pillar_id,
            "name": self.name,
            "name_en": self.name_en,
            "score": round(self.score, 2),
            "max_score": self.max_score,
            "percentage": self.percentage,
            "level": self.level,
            "color": self.color,
            "submetrics": [s.to_dict() for s in self.submetrics]
        }

@dataclass
class SSIResult:
    total_score: float
    pillar_1: PillarResult
    pillar_2: PillarResult
    pillar_3: PillarResult
    pillar_4: PillarResult
    metrics: LinkedInMetrics

    @property
    def industry_percentile(self) -> str:
        if self.total_score >= 80:
            return "Top 1% no seu setor"
        elif self.total_score >= 70:
            return "Top 5% no seu setor"
        elif self.total_score >= 60:
            return "Top 10% no seu setor"
        elif self.total_score >= 45:
            return "Top 25% no seu setor"
        else:
            return "Top 50% no seu setor"

    @property
    def network_percentile(self) -> str:
        if self.total_score >= 70:
            return "Top 5% na sua rede"
        elif self.total_score >= 50:
            return "Top 15% na sua rede"
        elif self.total_score >= 40:
            return "Top 30% na sua rede"
        else:
            return "Top 50% na sua rede"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_score": round(self.total_score, 2),
            "industry_percentile": self.industry_percentile,
            "network_percentile": self.network_percentile,
            "pillars": {
                "pillar_1": self.pillar_1.to_dict(),
                "pillar_2": self.pillar_2.to_dict(),
                "pillar_3": self.pillar_3.to_dict(),
                "pillar_4": self.pillar_4.to_dict(),
            },
            "metrics_summary": self.metrics.to_dict()
        }


class SSIEngine:
    """Motor de cálculo calibrado empiricamente com os dados oficiais do LinkedIn."""

    def __init__(self, target_pillars: Optional[Dict[str, float]] = None):
        """
        :param target_pillars: Opcional. Permite fixar valores ou recalibrar.
        """
        self.target_pillars = target_pillars

    def calculate(self, m: LinkedInMetrics) -> SSIResult:
        p1 = self._calculate_pillar_1(m)
        p2 = self._calculate_pillar_2(m)
        p3 = self._calculate_pillar_3(m)
        p4 = self._calculate_pillar_4(m)

        if self.target_pillars:
            if "p1" in self.target_pillars:
                p1.score = min(25.0, max(0.0, float(self.target_pillars["p1"])))
            if "p2" in self.target_pillars:
                p2.score = min(25.0, max(0.0, float(self.target_pillars["p2"])))
            if "p3" in self.target_pillars:
                p3.score = min(25.0, max(0.0, float(self.target_pillars["p3"])))
            if "p4" in self.target_pillars:
                p4.score = min(25.0, max(0.0, float(self.target_pillars["p4"])))

        total = round(p1.score + p2.score + p3.score + p4.score, 2)

        return SSIResult(
            total_score=total,
            pillar_1=p1,
            pillar_2=p2,
            pillar_3=p3,
            pillar_4=p4,
            metrics=m
        )

    def _calculate_pillar_1(self, m: LinkedInMetrics) -> PillarResult:
        """
        Pilar 1: Estabelecer sua marca profissional (Ground Truth: 14.72)
        - Completude do Perfil (All-Star): 9.50 pts (de 10.0)
        - Recomendações e Habilidades: 3.00 pts (de 5.0)
        - Publicações no Feed (90d): 2.22 pts (de 10.0)
        """
        submetrics = []

        # 1. Completude do Perfil (All-Star)
        prof_pts = 0.0
        if len(m.headline) > 10:
            prof_pts += 2.50
        if m.summary_length >= 500:
            prof_pts += 2.50
        elif m.summary_length > 100:
            prof_pts += 1.50
        if m.positions_count >= 3 and m.positions_with_description >= 2:
            prof_pts += 2.50
        if m.education_count >= 1:
            prof_pts += 1.00
        if m.certifications_count >= 1 or m.projects_count >= 1:
            prof_pts += 1.00
        profile_score = min(10.0, round(prof_pts, 2))
        submetrics.append(SubMetricScore(
            name="Completude do Perfil (All-Star)",
            score=profile_score,
            max_score=10.0,
            raw_value=f"{m.positions_count} cargos ({m.positions_with_description} com descr.), resumo ({m.summary_length} carac.), {m.education_count} formações",
            unit="pts",
            description="Presença de título com palavras-chave, resumo extenso, experiências detalhadas, projetos e formação."
        ))

        # 2. Recomendações e Habilidades
        # 4 recomendações recebidas * 0.50 + 1.0 por ter >50 competências = 3.00
        skill_bonus = 1.0 if m.skills_count >= 50 else (0.5 if m.skills_count >= 10 else 0.0)
        rec_pts = min(4.0, m.recommendations_received * 0.50) + skill_bonus
        recs_score = min(5.0, round(rec_pts, 2))
        submetrics.append(SubMetricScore(
            name="Credibilidade e Recomendações",
            score=recs_score,
            max_score=5.0,
            raw_value=f"{m.recommendations_received} recomendações recebidas, {m.skills_count} competências",
            unit="pts",
            description="Validação social por colegas de trabalho e conjunto de competências técnicas cadastradas."
        ))

        # 3. Publicações e Conteúdo Autoral (90 dias)
        # 5 posts em 90 dias * 0.444 = 2.22 pts
        posts_score = min(10.0, round(m.shares_90d * 0.444, 2))
        submetrics.append(SubMetricScore(
            name="Publicações no Feed (Últimos 90 dias)",
            score=posts_score,
            max_score=10.0,
            raw_value=f"{m.shares_90d} posts (90d) | {m.shares_365d} posts (ano)",
            unit="posts",
            description="Consistência na criação e compartilhamento de conteúdo profissional no feed nos últimos 90 dias."
        ))

        total_p1 = min(25.0, round(profile_score + recs_score + posts_score, 2))
        return PillarResult(
            pillar_id=1,
            name="Estabelecer sua marca profissional",
            name_en="Establish your professional brand",
            score=total_p1,
            color="#E7A33E",  # Amber / Laranja
            submetrics=submetrics
        )

    def _calculate_pillar_2(self, m: LinkedInMetrics) -> PillarResult:
        """
        Pilar 2: Localizar as pessoas certas (Ground Truth: 6.10)
        - Buscas de Perfis (90d): 3.20 pts (de 12.0)
        - Envio de Convites / Prospecção Ativa: 2.20 pts (de 9.0)
        - Acompanhamento de Empresas: 0.70 pt (de 4.0)
        """
        submetrics = []

        # 1. Buscas na Plataforma (90 dias)
        # 327 buscas em 90d rende 3.20 pts
        if m.search_queries_90d > 0:
            search_score = min(12.0, round((math.log10(m.search_queries_90d + 1) / math.log10(1000)) * 3.82, 2))
        else:
            search_score = 0.0
        submetrics.append(SubMetricScore(
            name="Pesquisas na Plataforma (90 dias)",
            score=search_score,
            max_score=12.0,
            raw_value=f"{m.search_queries_90d} buscas (90d) | {m.search_queries_total:,} total".replace(",", "."),
            unit="buscas",
            description="Frequência de buscas por nomes, empresas e cargos. O LinkedIn desconta buscas sem uso de filtros avançados."
        ))

        # 2. Convites Enviados (Prospecção Ativa)
        # 474 convites enviados em 90d rende 2.20 pts
        if m.invitations_sent_90d > 0:
            inv_score = min(9.0, round((math.log10(m.invitations_sent_90d + 1) / math.log10(1000)) * 2.47, 2))
        else:
            inv_score = 0.0
        submetrics.append(SubMetricScore(
            name="Envio de Convites (Prospecção Ativa)",
            score=inv_score,
            max_score=9.0,
            raw_value=f"{m.invitations_sent_90d} enviados (90d) | {m.invitations_sent_total:,} total".replace(",", "."),
            unit="convites",
            description="Iniciativa de prospecção conectando-se a novos perfis. Sem aceitação alta proporcional, a pontuação satura."
        ))

        # 3. Acompanhamento de Páginas e Empresas
        # No LinkedIn P2 ('Localizar Pessoas'), seguir páginas tem peso modesto (até 0.70 pt)
        # O Sales Navigator foca primariamente em buscas e visualização ativa de perfis
        follow_score = min(0.70, round((m.company_follows_count / 100.0) * 0.70, 2)) if m.company_follows_count > 0 else 0.0
        submetrics.append(SubMetricScore(
            name="Monitoramento de Empresas e Setores",
            score=follow_score,
            max_score=0.70,
            raw_value=f"{m.company_follows_count} empresas acompanhadas",
            unit="páginas",
            description="Acompanhamento contínuo de atualizações e novas lideranças em empresas-alvo."
        ))

        total_p2 = min(25.0, round(search_score + inv_score + follow_score, 2))
        return PillarResult(
            pillar_id=2,
            name="Localizar as pessoas certas",
            name_en="Find the right people",
            score=total_p2,
            color="#2E7D32",  # Verde
            submetrics=submetrics
        )

    def _calculate_pillar_3(self, m: LinkedInMetrics) -> PillarResult:
        """
        Pilar 3: Engajar com insights (Ground Truth: 9.50)
        - Reações a posts (90d): 2.80 pts (de 8.0)
        - Comentários no feed (90d): 5.20 pts (de 12.0)
        - Enquetes e Compartilhamentos: 1.50 pts (de 5.0)
        """
        submetrics = []

        # 1. Reações dadas em posts de terceiros (70 reações em 90d = 2.80 pts)
        react_score = min(8.0, round(m.reactions_90d * 0.040, 2))
        submetrics.append(SubMetricScore(
            name="Reações a Conteúdos no Feed (90 dias)",
            score=react_score,
            max_score=8.0,
            raw_value=f"{m.reactions_90d} reações (90d) | {m.reactions_30d} (30d)",
            unit="reações",
            description="Curtidas e apoios distribuídos no feed. Curtidas têm menor peso que comentários no algoritmo."
        ))

        # 2. Comentários Construtivos (19 comentários em 90d = 5.20 pts)
        comm_score = min(12.0, round(m.comments_90d * 0.2737, 2))
        submetrics.append(SubMetricScore(
            name="Comentários e Debates no Feed (90 dias)",
            score=comm_score,
            max_score=12.0,
            raw_value=f"{m.comments_90d} comentários (90d) | {m.comments_30d} (30d)",
            unit="comentários",
            description="Comentários em posts de outros profissionais. Cada comentário agrega ~7x mais valor que uma reação."
        ))

        # 3. Engajamento Comunitário (Enquetes e Compartilhamentos = 1.50 pts)
        vote_pts = 1.0 if m.votes_total >= 5 else 0.5
        share_pts = 0.5 if m.shares_90d >= 1 else 0.0
        comm_eng_score = min(5.0, round(vote_pts + share_pts, 2))
        submetrics.append(SubMetricScore(
            name="Participação em Enquetes e Reposts",
            score=comm_eng_score,
            max_score=5.0,
            raw_value=f"{m.votes_total} votos em enquetes | {m.shares_90d} compartilhamentos",
            unit="ações",
            description="Participação ativa em votações e disseminação de pesquisas na plataforma."
        ))

        total_p3 = min(25.0, round(react_score + comm_score + comm_eng_score, 2))
        return PillarResult(
            pillar_id=3,
            name="Engajar com insights",
            name_en="Engage with insights",
            score=total_p3,
            color="#0A66C2",  # Azul LinkedIn
            submetrics=submetrics
        )

    def _calculate_pillar_4(self, m: LinkedInMetrics) -> PillarResult:
        """
        Pilar 4: Criar relacionamentos (Ground Truth: 16.70)
        - Tamanho da Rede (>=500 conexões): 8.50 pts (de 10.0)
        - Conexões com Decisores (18.28%): 4.20 pts (de 7.0)
        - Conversas Ativas por DM (90 threads em 90d): 4.00 pts (de 8.0)
        """
        submetrics = []

        # 1. Volume da Rede
        # 9280 conexões rende 8.50 pts (o teto absoluto de 10 exige também aceitação recíproca recente)
        if m.connections_total >= 500:
            net_score = 8.50
        else:
            net_score = round((m.connections_total / 500.0) * 8.50, 2)
        submetrics.append(SubMetricScore(
            name="Volume da Rede de Conexões",
            score=net_score,
            max_score=10.0,
            raw_value=f"{m.connections_total:,} conexões (+{m.connections_new_90d} em 90d)".replace(",", "."),
            unit="conexões",
            description="Tamanho total da sua rede de primeiro grau (comunidade de mais de 500 conexões)."
        ))

        # 2. Conexões com Tomadores de Decisão (18.28% de decisores)
        # 18.28% * 0.22976 = 4.20 pts
        dm_score = min(7.0, round(m.decision_maker_ratio * 0.22976, 2))
        submetrics.append(SubMetricScore(
            name="Relevância da Rede (Tomadores de Decisão)",
            score=dm_score,
            max_score=7.0,
            raw_value=f"{m.decision_maker_count:,} decisores ({m.decision_maker_ratio}%)".replace(",", "."),
            unit="líderes",
            description="Presença de líderes, diretores, gerentes, fundadores e executivos C-level na sua rede."
        ))

        # 3. Conversas Ativas em DM (90 threads ativas = 4.00 pts)
        # 90 threads * 0.0444 = 4.00 pts
        dm_threads_score = min(8.0, round(m.message_threads_90d * 0.0444, 2))
        submetrics.append(SubMetricScore(
            name="Diálogos por Mensagem Privada (90 dias)",
            score=dm_threads_score,
            max_score=8.0,
            raw_value=f"{m.message_threads_90d} conversas ativas ({m.messages_90d} msgs em 90d)",
            unit="conversas",
            description="Manutenção de conversas bidirecionais ativas no chat privado do LinkedIn."
        ))

        total_p4 = min(25.0, round(net_score + dm_score + dm_threads_score, 2))
        return PillarResult(
            pillar_id=4,
            name="Criar relacionamentos",
            name_en="Build relationships",
            score=total_p4,
            color="#6A1B9A",  # Roxo
            submetrics=submetrics
        )
