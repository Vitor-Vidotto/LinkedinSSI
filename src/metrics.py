"""
metrics.py - Extrator de Métricas e Features Brutas do LinkedIn.
Calcula contagens, janelas temporais (30d, 90d, 365d), completude de perfil e cargos.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import pandas as pd
from .parser import LinkedInDataParser

DECISION_MAKER_KEYWORDS = [
    "diretor", "director", "ceo", "founder", "fundador", "co-founder", "co-fundador",
    "vp", "vice president", "vice-presidente", "head", "gerente", "manager",
    "sócio", "socio", "partner", "owner", "proprietário", "lead", "lider", "líder",
    "cto", "cfo", "cio", "cmo", "coo", "cpo", "cro", "chief"
]

@dataclass
class LinkedInMetrics:
    """Estrutura com todas as métricas brutas extraídas da exportação."""
    reference_date: datetime
    
    # Perfil / P1
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    summary_length: int = 0
    positions_count: int = 0
    positions_with_description: int = 0
    education_count: int = 0
    skills_count: int = 0
    certifications_count: int = 0
    projects_count: int = 0
    recommendations_received: int = 0
    recommendations_given: int = 0
    endorsements_received: int = 0
    rich_media_count: int = 0
    shares_30d: int = 0
    shares_90d: int = 0
    shares_365d: int = 0
    shares_total: int = 0

    # Buscas e Prospecção / P2
    search_queries_30d: int = 0
    search_queries_90d: int = 0
    search_queries_365d: int = 0
    search_queries_total: int = 0
    invitations_sent_30d: int = 0
    invitations_sent_90d: int = 0
    invitations_sent_total: int = 0
    invitations_received_30d: int = 0
    invitations_received_90d: int = 0
    invitations_received_total: int = 0
    company_follows_count: int = 0
    member_follows_count: int = 0

    # Engajamento / P3
    reactions_30d: int = 0
    reactions_90d: int = 0
    reactions_365d: int = 0
    reactions_total: int = 0
    reactions_types: Dict[str, int] = field(default_factory=dict)
    comments_30d: int = 0
    comments_90d: int = 0
    comments_365d: int = 0
    comments_total: int = 0
    votes_total: int = 0

    # Relacionamentos / P4
    connections_total: int = 0
    connections_new_30d: int = 0
    connections_new_90d: int = 0
    connections_new_365d: int = 0
    decision_maker_count: int = 0
    decision_maker_ratio: float = 0.0
    messages_total: int = 0
    messages_30d: int = 0
    messages_90d: int = 0
    message_threads_90d: int = 0
    message_threads_total: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte as métricas para dicionário serializável."""
        d = self.__dict__.copy()
        d["reference_date"] = self.reference_date.isoformat()
        return d


class MetricsExtractor:
    """Extrai as métricas de um LinkedInDataParser."""

    def __init__(self, parser: LinkedInDataParser, reference_date: Optional[datetime] = None):
        self.parser = parser
        self.reference_date = reference_date

    def _parse_dates(self, series: pd.Series) -> pd.Series:
        """Converte uma coluna de datas de múltiplos formatos para UTC timestamp."""
        if series.empty:
            return pd.Series(dtype="datetime64[ns, UTC]")
        return pd.to_datetime(series, errors="coerce", utc=True, format="mixed")

    def extract(self) -> LinkedInMetrics:
        """Processa todos os CSVs e retorna um objeto LinkedInMetrics consolidado."""
        # 1. Carrega os DataFrames necessários
        profile_df = self.parser.get_df("profile")
        positions_df = self.parser.get_df("positions")
        education_df = self.parser.get_df("education")
        skills_df = self.parser.get_df("skills")
        certs_df = self.parser.get_df("certifications")
        projects_df = self.parser.get_df("projects")
        recs_rec_df = self.parser.get_df("recommendations_received")
        recs_giv_df = self.parser.get_df("recommendations_given")
        endorse_rec_df = self.parser.get_df("endorsement_received_info")
        rich_media_df = self.parser.get_df("rich_media")

        shares_df = self.parser.get_df("shares")
        reactions_df = self.parser.get_df("reactions")
        comments_df = self.parser.get_df("comments")
        search_df = self.parser.get_df("searchqueries")
        invites_df = self.parser.get_df("invitations")
        messages_df = self.parser.get_df("messages")
        connections_df = self.parser.get_df("connections")
        company_df = self.parser.get_df("company follows")
        member_df = self.parser.get_df("member_follows")
        votes_df = self.parser.get_df("votes")

        # 2. Parse de datas dos eventos dinâmicos
        shares_dt = self._parse_dates(shares_df["Date"]) if not shares_df.empty and "Date" in shares_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        reactions_dt = self._parse_dates(reactions_df["Date"]) if not reactions_df.empty and "Date" in reactions_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        comments_dt = self._parse_dates(comments_df["Date"]) if not comments_df.empty and "Date" in comments_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        search_dt = self._parse_dates(search_df["Time"]) if not search_df.empty and "Time" in search_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        invites_dt = self._parse_dates(invites_df["Sent At"]) if not invites_df.empty and "Sent At" in invites_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        messages_dt = self._parse_dates(messages_df["DATE"]) if not messages_df.empty and "DATE" in messages_df.columns else pd.Series(dtype="datetime64[ns, UTC]")
        connections_dt = self._parse_dates(connections_df["Connected On"]) if not connections_df.empty and "Connected On" in connections_df.columns else pd.Series(dtype="datetime64[ns, UTC]")

        # 3. Determinação da Data de Referência (data máxima observada na exportação ou data informada)
        if self.reference_date is None:
            candidate_dates = []
            for dt_series in [shares_dt, reactions_dt, comments_dt, search_dt, invites_dt, messages_dt, connections_dt]:
                if not dt_series.empty:
                    valid_dts = dt_series.dropna()
                    if not valid_dts.empty:
                        candidate_dates.append(valid_dts.max())

            if candidate_dates:
                ref_dt = max(candidate_dates).to_pydatetime()
            else:
                ref_dt = datetime.now(timezone.utc)
        else:
            ref_dt = self.reference_date
            if ref_dt.tzinfo is None:
                ref_dt = ref_dt.replace(tzinfo=timezone.utc)

        # Datas de corte
        d30 = ref_dt - timedelta(days=30)
        d90 = ref_dt - timedelta(days=90)
        d365 = ref_dt - timedelta(days=365)

        # 4. Extração P1: Perfil
        first_name = ""
        last_name = ""
        headline = ""
        summary_len = 0
        if not profile_df.empty:
            first_name = str(profile_df["First Name"].iloc[0]) if "First Name" in profile_df.columns and pd.notna(profile_df["First Name"].iloc[0]) else ""
            last_name = str(profile_df["Last Name"].iloc[0]) if "Last Name" in profile_df.columns and pd.notna(profile_df["Last Name"].iloc[0]) else ""
            headline = str(profile_df["Headline"].iloc[0]) if "Headline" in profile_df.columns and pd.notna(profile_df["Headline"].iloc[0]) else ""
            if "Summary" in profile_df.columns and pd.notna(profile_df["Summary"].iloc[0]):
                summary_len = len(str(profile_df["Summary"].iloc[0]))

        pos_count = len(positions_df) if not positions_df.empty else 0
        pos_with_desc = positions_df["Description"].dropna().count() if not positions_df.empty and "Description" in positions_df.columns else 0
        edu_count = len(education_df) if not education_df.empty else 0
        skills_count = len(skills_df) if not skills_df.empty else 0
        certs_count = len(certs_df) if not certs_df.empty else 0
        proj_count = len(projects_df) if not projects_df.empty else 0
        recs_rec = len(recs_rec_df) if not recs_rec_df.empty else 0
        recs_giv = len(recs_giv_df) if not recs_giv_df.empty else 0
        endorse_rec = len(endorse_rec_df) if not endorse_rec_df.empty else 0
        rich_media = len(rich_media_df) if not rich_media_df.empty else 0

        shares_30d = int((shares_dt >= d30).sum()) if not shares_dt.empty else 0
        shares_90d = int((shares_dt >= d90).sum()) if not shares_dt.empty else 0
        shares_365d = int((shares_dt >= d365).sum()) if not shares_dt.empty else 0
        shares_total = len(shares_df) if not shares_df.empty else 0

        # 5. Extração P2: Buscas e Convites
        sq_30d = int((search_dt >= d30).sum()) if not search_dt.empty else 0
        sq_90d = int((search_dt >= d90).sum()) if not search_dt.empty else 0
        sq_365d = int((search_dt >= d365).sum()) if not search_dt.empty else 0
        sq_total = len(search_df) if not search_df.empty else 0

        inv_out = (invites_df["Direction"] == "OUTGOING") if not invites_df.empty and "Direction" in invites_df.columns else pd.Series(False, index=invites_df.index)
        inv_sent_30d = int(((invites_dt >= d30) & inv_out).sum()) if not invites_dt.empty else 0
        inv_sent_90d = int(((invites_dt >= d90) & inv_out).sum()) if not invites_dt.empty else 0
        inv_sent_total = int(inv_out.sum()) if not invites_df.empty else 0

        inv_in = (invites_df["Direction"] == "INCOMING") if not invites_df.empty and "Direction" in invites_df.columns else pd.Series(False, index=invites_df.index)
        inv_rec_30d = int(((invites_dt >= d30) & inv_in).sum()) if not invites_dt.empty else 0
        inv_rec_90d = int(((invites_dt >= d90) & inv_in).sum()) if not invites_dt.empty else 0
        inv_rec_total = int(inv_in.sum()) if not invites_df.empty else 0

        comp_count = len(company_df) if not company_df.empty else 0
        mem_count = len(member_df) if not member_df.empty else 0

        # 6. Extração P3: Engajamento
        react_30d = int((reactions_dt >= d30).sum()) if not reactions_dt.empty else 0
        react_90d = int((reactions_dt >= d90).sum()) if not reactions_dt.empty else 0
        react_365d = int((reactions_dt >= d365).sum()) if not reactions_dt.empty else 0
        react_total = len(reactions_df) if not reactions_df.empty else 0
        react_types = reactions_df["Type"].value_counts().to_dict() if not reactions_df.empty and "Type" in reactions_df.columns else {}

        comm_30d = int((comments_dt >= d30).sum()) if not comments_dt.empty else 0
        comm_90d = int((comments_dt >= d90).sum()) if not comments_dt.empty else 0
        comm_365d = int((comments_dt >= d365).sum()) if not comments_dt.empty else 0
        comm_total = len(comments_df) if not comments_df.empty else 0
        votes_count = len(votes_df) if not votes_df.empty else 0

        # 7. Extração P4: Relacionamentos e Conexões
        conn_total = len(connections_df) if not connections_df.empty else 0
        conn_30d = int((connections_dt >= d30).sum()) if not connections_dt.empty else 0
        conn_90d = int((connections_dt >= d90).sum()) if not connections_dt.empty else 0
        conn_365d = int((connections_dt >= d365).sum()) if not connections_dt.empty else 0

        dm_count = 0
        dm_ratio = 0.0
        if not connections_df.empty and "Position" in connections_df.columns:
            positions_series = connections_df["Position"].dropna().str.lower()
            if len(positions_series) > 0:
                is_dm = positions_series.apply(lambda p: any(k in p for k in DECISION_MAKER_KEYWORDS))
                dm_count = int(is_dm.sum())
                dm_ratio = round((dm_count / len(positions_series)) * 100, 2)

        msg_total = len(messages_df) if not messages_df.empty else 0
        msg_30d = int((messages_dt >= d30).sum()) if not messages_dt.empty else 0
        msg_90d = int((messages_dt >= d90).sum()) if not messages_dt.empty else 0

        threads_total = 0
        threads_90d = 0
        if not messages_df.empty and "CONVERSATION ID" in messages_df.columns:
            threads_total = int(messages_df["CONVERSATION ID"].nunique())
            if not messages_dt.empty:
                m_90d_df = messages_df[messages_dt >= d90]
                threads_90d = int(m_90d_df["CONVERSATION ID"].nunique())

        return LinkedInMetrics(
            reference_date=ref_dt,
            first_name=first_name,
            last_name=last_name,
            headline=headline,
            summary_length=summary_len,
            positions_count=pos_count,
            positions_with_description=int(pos_with_desc),
            education_count=edu_count,
            skills_count=skills_count,
            certifications_count=certs_count,
            projects_count=proj_count,
            recommendations_received=recs_rec,
            recommendations_given=recs_giv,
            endorsements_received=endorse_rec,
            rich_media_count=rich_media,
            shares_30d=shares_30d,
            shares_90d=shares_90d,
            shares_365d=shares_365d,
            shares_total=shares_total,
            search_queries_30d=sq_30d,
            search_queries_90d=sq_90d,
            search_queries_365d=sq_365d,
            search_queries_total=sq_total,
            invitations_sent_30d=inv_sent_30d,
            invitations_sent_90d=inv_sent_90d,
            invitations_sent_total=inv_sent_total,
            invitations_received_30d=inv_rec_30d,
            invitations_received_90d=inv_rec_90d,
            invitations_received_total=inv_rec_total,
            company_follows_count=comp_count,
            member_follows_count=mem_count,
            reactions_30d=react_30d,
            reactions_90d=react_90d,
            reactions_365d=react_365d,
            reactions_total=react_total,
            reactions_types=react_types,
            comments_30d=comm_30d,
            comments_90d=comm_90d,
            comments_365d=comm_365d,
            comments_total=comm_total,
            votes_total=votes_count,
            connections_total=conn_total,
            connections_new_30d=conn_30d,
            connections_new_90d=conn_90d,
            connections_new_365d=conn_365d,
            decision_maker_count=dm_count,
            decision_maker_ratio=dm_ratio,
            messages_total=msg_total,
            messages_30d=msg_30d,
            messages_90d=msg_90d,
            message_threads_90d=threads_90d,
            message_threads_total=threads_total
        )
