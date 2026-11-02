# 📊 Projeto: Calculadora Open-Source de LinkedIn SSI (Social Selling Index)

## 1. Visão Geral do Projeto
O objetivo deste projeto é construir uma aplicação capaz de estimar com alta precisão o **Social Selling Index (SSI)** de qualquer usuário do LinkedIn de forma gratuita, sem a necessidade de assinar o LinkedIn Sales Navigator (atualmente ~R$ 300/mês). 

A solução funcionará processando o pacote de dados oficial que o próprio LinkedIn disponibiliza gratuitamente para qualquer usuário (via *Configurações > Privacidade dos Dados > Obter cópia dos seus dados*).

* **Ambiente de Desenvolvimento:** Antigravity (Python / Web Stack)
* **Benchmark Inicial (Ground Truth):** Score `49` (baseado no pacote de dados real do criador do projeto).

---

## 2. Entendendo a Matemática do SSI
O SSI varia de $0$ a $100$ e é dividido igualmente em **4 pilares**, onde cada pilar vale de $0$ a $25$ pontos:

$$\text{SSI Total} = P_1 + P_2 + P_3 + P_4 \quad \text{onde } P_i \in [0, 25]$$

1. **$P_1$: Estabelecer sua marca profissional (Establish your professional brand)**
   * Foco: Completude do perfil, uso de mídia, artigos publicados, postagens e recomendações recebidas.
2. **$P_2$: Localizar as pessoas certas (Find the right people)**
   * Foco: Buscas realizadas, visualizações de perfis estratégicos, uso de filtros e conexões de 2º grau alcançadas.
3. **$P_3$: Interagir oferecendo insights (Engage with insights)**
   * Foco: Compartilhamento de conteúdo, reações dadas/recebidas, comentários em posts de terceiros, engajamento em grupos.
4. **$P_4$: Cultivar relacionamentos (Build relationships)**
   * Foco: Tamanho da rede, taxa de aceitação de convites enviados, interações por mensagem direta (`messages.csv`) e conexões com tomadores de decisão (cargos de liderança: Diretor, VP, C-Level).

---

## 3. Mapeamento dos Dados (O Arquivo `.zip` do LinkedIn)
Quando o usuário baixa seus dados do LinkedIn, ele recebe um arquivo `.zip` contendo diversos arquivos `.csv`. Abaixo estão os arquivos críticos que nosso parser no Antigravity precisará ler:

| Arquivo no `.zip` | Pilar Afetado | O que extrair (Features) |
| :--- | :---: | :--- |
| `Profile.csv` | $P_1$ | Presença de Headline, Summary (tamanho do texto), Industry. |
| `Positions.csv` | $P_1$ | Quantidade de experiências cadastradas e se possuem descrição. |
| `Education.csv` / `Skills.csv` | $P_1$ | Quantidade de habilidades listadas (o LinkedIn valoriza $>5$ skills) e formação. |
| `Recommendations_Received.csv` | $P_1$ | Contagem total de recomendações recebidas. |
| `Shares.csv` | $P_1, P_3$ | Frequência de postagens nos últimos 90 e 365 dias. |
| `SearchQueries.csv` | $P_2$ | Volume de buscas feitas na plataforma nos últimos 90 dias. |
| `Invitations.csv` | $P_2, P_4$ | Proporção de convites enviados (`SENT`) vs recebidos (`RECEIVED`). |
| `Reactions.csv` / `Comments.csv` | $P_3$ | Volume de interações (likes, aplausos, comentários) nos últimos 90 dias. |
| `Connections.csv` | $P_4$ | Total de conexões, crescimento recente (coluna `Connected On`) e cargos das conexões (coluna `Position` -> detectar seniors/decisores). |
| `messages.csv` | $P_3, P_4$ | Frequência de trocas de mensagens (conversas iniciadas e respondidas). |

> **⚠️ Nota Importante sobre Temporalidade:** O SSI do LinkedIn é uma métrica **dinâmica e rolante** (rolling window). Atividades feitas há 3 anos quase não contam para os pilares $P_2$ e $P_3$. Nosso código precisará filtrar `Shares`, `Reactions`, `Comments`, `Invitations` e `messages` aplicando um peso maior para os **últimos 30 a 90 dias** anteriores à data de exportação do arquivo!

---

## 4. Engenharia Reversa da Fórmula (Calibração no Score 49)

Para chegarmos ao seu score de **49**, vamos criar funções de pontuação saturadas (usando funções logarítmicas ou limites máximos/caps, pois ter 5.000 conexões não dá o dobro de pontos de ter 2.500 conexões — existe um teto).

### 4.1. Pilar 1: Marca Profissional (Máx: 25 pts)
$$P_1 = w_{1a}(\text{Completude}) + w_{1b}(\text{Recomendações}) + w_{1c}(\text{Publicações})$$
* **Completude do Perfil (até 10 pts):** Tem resumo preenchido (+3), tem $>3$ experiências (+3), tem $>10$ skills (+2), tem formação (+2).
* **Recomendações (até 5 pts):** $\min(5, \text{Total de Recomendações} \times 1.5)$.
* **Publicações (`Shares.csv` últimos 90 dias) (até 10 pts):** $\min(10, \text{Posts}_{90d} \times 1.0)$.

### 4.2. Pilar 2: Localizar as Pessoas Certas (Máx: 25 pts)
$$P_2 = w_{2a}(\text{Buscas}_{90d}) + w_{2b}(\text{Convites Enviados}_{90d})$$
* **Buscas (`SearchQueries.csv` últimos 90 dias) (até 15 pts):** $\min(15, \text{Buscas}_{90d} \times 0.25)$.
* **Prospecção Ativa (`Invitations.csv` tipo OUTGOING 90d) (até 10 pts):** $\min(10, \text{Convites Enviados}_{90d} \times 0.4)$.

### 4.3. Pilar 3: Interagir com Insights (Máx: 25 pts)
$$P_3 = w_{3a}(\text{Reações}_{90d}) + w_{3b}(\text{Comentários}_{90d}) + w_{3c}(\text{Shares}_{90d})$$
* **Reações (`Reactions.csv` 90d) (até 10 pts):** $\min(10, \text{Likes}_{90d} \times 0.15)$.
* **Comentários (`Comments.csv` 90d) (até 10 pts):** Comentários valem muito mais que likes no algoritmo do LinkedIn. $\min(10, \text{Comments}_{90d} \times 0.5)$.
* **Compartilhamentos (até 5 pts):** Bônus por compartilhar links/insights.

### 4.4. Pilar 4: Cultivar Relacionamentos (Máx: 25 pts)
$$P_4 = w_{4a}(\text{Tamanho da Rede}) + w_{4b}(\text{Qualidade/Cargos}) + w_{4c}(\text{Mensagens}_{90d})$$
* **Tamanho da Rede (`Connections.csv`) (até 10 pts):** Escala até 500 conexões (teto padrão do LinkedIn). $\min(10, (\text{Total Conexões} / 500) \times 10)$.
* **Conexões com Decisores (até 5 pts):** % de conexões cujo `Position` contém palavras-chave como `Director`, `Diretor`, `CEO`, `Founder`, `VP`, `Head`, `Gerente`, `Manager`, `Sócio`.
* **Conversas em DM (`messages.csv` 90d) (até 10 pts):** $\min(10, \text{Threads Ativas}_{90d} \times 0.5)$.

---

## 5. Plano de Implementação (Passo a Passo no Antigravity)

### Fase 1: Exploração e Calibração (O seu Dataset = Score 49)
1. **Inspeção do seu `.zip`:** Colocar os seus arquivos CSV em uma pasta `/data/sample_user_49/` no projeto.
2. **Script de Extração de Métricas Brutas (`extractor.py`):**
   * Criar um script Python (usando `pandas` ou `csv` nativo) que lê todos os arquivos da pasta e imprime um JSON com os números brutos (Ex: `total_connections: 640`, `reactions_last_90d: 42`, `comments_last_90d: 8`, etc.).
3. **Ajuste Fino dos Pesos (`calibrator.py`):**
   * Olhar para os seus números brutos e ajustar os multiplicadores da Seção 4 para que a soma dos 4 pilares dê exatamente **49** (e que a distribuição entre os 4 pilares faça sentido com o seu comportamento real no LinkedIn).

### Fase 2: Construção do Core Engine (Backend)
1. **Módulo de Upload Seguro:**
   * O usuário não precisa descompactar o arquivo. Ele faz o upload direto do `Basic_LinkedInDataExport_XX-XX-XXXX.zip`.
   * Usar a biblioteca `zipfile` do Python em memória (`io.BytesIO`) para ler os CSVs sem precisar salvar os dados privados das pessoas no disco do servidor (excelente argumento de privacidade/LGPD!).
2. **Tratamento de Exceções:**
   * Se um usuário nunca publicou nada, o arquivo `Shares.csv` pode não existir dentro do `.zip`. O código deve tratar arquivos ausentes assumindo pontuação `0` para aquela métrica específica, sem quebrar a aplicação.
   * Tratamento das primeiras linhas do `Connections.csv` (o LinkedIn costuma colocar 3 linhas de aviso de texto antes do cabeçalho real do CSV nesse arquivo específico!).

### Fase 3: Interface Gráfica e Plano de Ação (Frontend)
1. **Dashboard Estilo Sales Navigator:**
   * Um gráfico de rosca (Gauge Chart / Donut Chart) mostrando o Score Total de $0$ a $100$.
   * Barras de progresso para os 4 pilares ($0$ a $25$ cada) com as mesmas cores do LinkedIn (Laranja, Roxo, Azul, Verde).
2. **Gerador de Recomendações (O Grande Diferencial):**
   * Além de dar a nota, o sistema analisa onde a pessoa perdeu pontos e gera um checklist prático.
   * *Exemplo:* "Você tem apenas 3 pontos em 'Interagir oferecendo insights'. Se você fizer 2 comentários por semana nos próximos 30 dias, seu SSI subirá aproximadamente +8 pontos."

---

## 6. Estrutura de Diretórios Sugerida

```text
linkedin-ssi-calculator/
├── data/
│   └── ground_truth_49/       # Seus CSVs para testes locais (no .gitignore!)
├── src/
│   ├── parser.py              # Lê o .zip em memória e limpa os CSVs
│   ├── metrics.py             # Calcula contagens (90 dias, histórico, keywords)
│   ├── ssi_engine.py          # Aplica os pesos matemáticos e retorna os 4 pilares
│   └── recommendations.py     # Gera dicas baseadas nos pilares mais fracos
├── app.py                     # Interface Web (Streamlit, FastAPI ou Flask/React)
├── requirements.txt
└── README.md
```

---

## 7. Próximos Passos Imediatos
1. **Verificar o link gratuito:** Acesse `https://www.linkedin.com/sales/ssi` hoje mesmo para ver qual é a sua nota exata atual e **qual é a nota individual de cada um dos seus 4 pilares** (tire um print dessa tela!). Ter a nota quebrada nos 4 pilares vai deixar a nossa engenharia reversa 10x mais precisa do que ter apenas o número 49.
2. **Listar os arquivos do seu ZIP:** Me diga quais arquivos `.csv` vieram dentro do pacote de dados que você baixou, e nós já podemos escrever o primeiro script Python para extrair os seus números brutos!