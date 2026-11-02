"""
parser.py - Leitor e Sanitizador de Arquivos de Exportação do LinkedIn.
Suporta tanto diretório descompactado quanto arquivo .zip diretamente.
"""

import os
import io
import re
import zipfile
import logging
from typing import Optional, Union, Dict, List
import pandas as pd

logger = logging.getLogger("linkedin_ssi.parser")

class LinkedInDataParser:
    """
    Carrega e extrai os DataFrames dos arquivos CSV da exportação do LinkedIn,
    lidando com variações de nomenclatura (ex: Shares_1050344536.csv vs Shares.csv),
    cabeçalhos especiais (como as 3 linhas de aviso no Connections.csv) e
    linhas corrompidas/desformatadas.
    """

    def __init__(self, source: Union[str, io.BytesIO]):
        """
        :param source: Caminho para pasta descompactada, caminho para arquivo .zip,
                       ou stream io.BytesIO de um arquivo .zip.
        """
        self.source = source
        self.is_zip = False
        self._zip_ref: Optional[zipfile.ZipFile] = None
        self._dir_path: Optional[str] = None
        self._file_index: Dict[str, str] = {}
        self._cache: Dict[str, pd.DataFrame] = {}

        self._initialize()

    def _initialize(self):
        if isinstance(self.source, io.BytesIO):
            self.is_zip = True
            self._zip_ref = zipfile.ZipFile(self.source, "r")
            self._index_zip_files()
        elif isinstance(self.source, str):
            if os.path.isdir(self.source):
                self.is_zip = False
                self._dir_path = os.path.abspath(self.source)
                self._index_dir_files()
            elif os.path.isfile(self.source) and (self.source.endswith(".zip") or zipfile.is_zipfile(self.source)):
                self.is_zip = True
                self._zip_ref = zipfile.ZipFile(self.source, "r")
                self._index_zip_files()
            else:
                raise ValueError(f"Fonte inválida ou inexistente: {self.source}")
        else:
            raise TypeError("Fonte deve ser caminho de arquivo/pasta ou io.BytesIO")

    def _index_zip_files(self):
        """Indexa os arquivos dentro do ZIP mapeando nomes limpos para o path interno."""
        for item in self._zip_ref.namelist():
            if item.lower().endswith(".csv"):
                base_name = os.path.basename(item)
                self._file_index[base_name.lower()] = item

    def _index_dir_files(self):
        """Indexa todos os arquivos CSV do diretório e subpastas."""
        for root, _, files in os.walk(self._dir_path):
            for file in files:
                if file.lower().endswith(".csv"):
                    full_path = os.path.join(root, file)
                    base_name = file.lower()
                    self._file_index[base_name] = full_path

    def _find_matching_key(self, pattern: str) -> Optional[str]:
        """
        Localiza a chave do arquivo correspondente no índice,
        suportando prefixos com ID do membro (ex: 'shares' encontra 'shares_1050344536.csv').
        """
        pattern_clean = pattern.lower().replace(".csv", "")
        # 1. Correspondência exata
        exact_csv = f"{pattern_clean}.csv"
        if exact_csv in self._file_index:
            return self._file_index[exact_csv]

        # 2. Correspondência com sufixo (ex: shares_12345.csv)
        regex_pattern = re.compile(rf"^{re.escape(pattern_clean)}(_.*)?\.csv$", re.IGNORECASE)
        for key, full_loc in self._file_index.items():
            if regex_pattern.match(key):
                return full_loc

        # 3. Correspondência contendo nome (fallback)
        for key, full_loc in self._file_index.items():
            if pattern_clean in key:
                return full_loc

        return None

    def get_df(self, file_identifier: str, skiprows: Optional[int] = None) -> pd.DataFrame:
        """
        Lê e retorna um DataFrame do arquivo solicitado.
        Se o arquivo não existir na exportação, retorna um DataFrame vazio.
        """
        ident_lower = file_identifier.lower()
        if ident_lower in self._cache:
            return self._cache[ident_lower]

        file_loc = self._find_matching_key(file_identifier)
        if not file_loc:
            # Arquivo opcional ausente na exportação do usuário
            df_empty = pd.DataFrame()
            self._cache[ident_lower] = df_empty
            return df_empty

        # Casos especiais de cabeçalho (ex: Connections.csv tem 3 linhas de aviso no topo)
        actual_skiprows = skiprows
        if actual_skiprows is None and "connection" in ident_lower:
            actual_skiprows = 3

        try:
            if self.is_zip:
                with self._zip_ref.open(file_loc) as f:
                    content_bytes = f.read()
                    try:
                        df = pd.read_csv(
                            io.BytesIO(content_bytes),
                            skiprows=actual_skiprows or 0,
                            on_bad_lines="skip",
                            encoding="utf-8"
                        )
                    except UnicodeDecodeError:
                        df = pd.read_csv(
                            io.BytesIO(content_bytes),
                            skiprows=actual_skiprows or 0,
                            on_bad_lines="skip",
                            encoding="latin-1"
                        )
            else:
                try:
                    df = pd.read_csv(
                        file_loc,
                        skiprows=actual_skiprows or 0,
                        on_bad_lines="skip",
                        encoding="utf-8"
                    )
                except UnicodeDecodeError:
                    df = pd.read_csv(
                        file_loc,
                        skiprows=actual_skiprows or 0,
                        on_bad_lines="skip",
                        encoding="latin-1"
                    )

            # Higienização de nomes de colunas
            df.columns = [str(c).strip() for c in df.columns]
            self._cache[ident_lower] = df
            return df

        except Exception as e:
            logger.warning(f"Erro ao ler CSV '{file_identifier}' ({file_loc}): {e}")
            df_empty = pd.DataFrame()
            self._cache[ident_lower] = df_empty
            return df_empty

    def list_available_files(self) -> List[str]:
        """Retorna a lista de nomes amigáveis de todos os CSVs encontrados."""
        return sorted(list(self._file_index.keys()))

    def close(self):
        """Fecha manipuladores de arquivos abertos."""
        if self._zip_ref:
            try:
                self._zip_ref.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
