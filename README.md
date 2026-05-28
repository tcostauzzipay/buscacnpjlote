# 💼 Consulta e Enriquecimento de CNPJs

Este projeto consiste em um aplicativo para o enriquecimento em lote de cadastros de CNPJs brasileiros de forma automatizada, utilizando a API pública e estável do **BrasilAPI**.

---

## ✨ Funcionalidades Principais

* **📤 Upload de Arquivos Multiprodutos**: Suporte nativo para carregar arquivos nos formatos `.csv`, `.xlsx`, `.xls` ou `.txt`. O aplicativo detecta automaticamente a coluna que contém os CNPJs e exibe uma prévia interativa dos dados inseridos.
* **📝 Área de Colagem Direta (Clipboard)**: Permite colar listas de CNPJs em bloco (separados por quebras de linha, vírgulas, espaços ou ponto-e-vírgula). O script limpa caracteres especiais, remove pontuações (`.`, `/`, `-`) e extrai automaticamente apenas sequências válidas de 14 dígitos.
* **🚫 Limite de Segurança de 200 CNPJs**: Validação automatizada que limita o processamento a **no máximo 200 CNPJs únicos por consulta**, evitando sobrecargas no servidor e prevenindo que a chave de IP seja bloqueada por rate-limiting.
* **⚙️ Parâmetros de Requisição Administrativos (Bloqueados)**: As variáveis de desempenho de requisição na barra lateral estão **travadas administrativamente** para evitar alterações acidentais de usuários que possam causar instabilidade.
  * **Delay de requisições:** `0.2 segundos` (intervalo padrão entre chamadas).
  * **Pausa para estabilização:** `5 segundos` a cada `100 consultas`.
  * **Tempo de retenção (Rate Limit 429):** `30 segundos` de pausa antes de tentar novamente em caso de bloqueio temporário.
* **🔍 Colunas de Retorno Reordenadas**: Coleta e mapeamento de **16 colunas solicitadas**. A coluna **`opcao_pelo_simples`** está posicionada de forma privilegiada em **segundo lugar** na planilha, logo após o campo **`cnpj`** para facilitar a análise imediata.
* **📊 Painel de Métricas (Dashboard)**: Apresentação de dados estatísticos do processamento finalizado (Total processado, Encontrados/Válidos, Não encontrados, Erros e Taxa de sucesso %).
* **🛑 Botão de Interrupção Seguro (Stop)**: Permite parar as requisições a qualquer momento. Os dados já coletados até o momento da parada são **totalmente preservados**, permitindo filtragem e download imediatos.
* **🎯 Filtros Dinâmicos no Painel**:
  * Pesquisa textual de empresas por **Razão Social / Nome Fantasia**.
  * Pesquisa de endereço por **Logradouro / Bairro / UF**.
  * Seleção suspensa dinâmica por **Situação Cadastral** e **Porte da Empresa**.
  * Seleção dinâmica por **Opção pelo Simples** e **Opção pelo MEI** (Sim/Não).
* **💾 Exportação de Alto Padrão**:
  * **Excel (.xlsx):** Planilha com colunas auto-dimensionadas ao conteúdo e cabeçalhos coloridos em tons corporativos e elegantes.
  * **CSV:** Separado por ponto-e-vírgula (`;`) com cabeçalho delimitado por aspas e formato `utf-8-sig` (compatibilidade 100% nativa para abrir diretamente no Microsoft Excel sem corromper acentos).

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.13+**
* **Streamlit** (Framework de UI Web)
* **Pandas** (Estruturação e manipulação de dados)
* **Requests** (Consumo da API Rest BrasilAPI)
* **xlsxwriter / openpyxl** (Geração e estilização de planilhas Excel avançadas)

---

## 🚀 Como Instalar e Rodar o Aplicativo

### 1. Pré-requisitos
Certifique-se de que os pacotes necessários estão instalados em seu ambiente Python:

```bash
pip install streamlit pandas requests openpyxl xlsxwriter
```

### 2. Executar o Aplicativo Streamlit
Navegue até a pasta do projeto no seu terminal/PowerShell e execute o comando abaixo:

```bash
streamlit run enrich_streamlit.py
```

O navegador abrirá automaticamente o endereço local: `http://localhost:8501`.

---

## 📂 Estrutura do Arquivo de Entrada (Exemplo CSV)

Se você preferir carregar um arquivo CSV para a consulta, certifique-se de que ele possua uma coluna nomeada com `cnpj` (ou similar). 
Exemplo de formato aceito:

```csv
cnpjs
10385218000165
10473109000108
10692111000160
```

---

## 📋 Mapeamento de Colunas de Saída

As 16 colunas padrão retornadas no enriquecimento de dados são ordenadas da seguinte forma:

1. **`cnpj`**
2. **`opcao_pelo_simples`** (Sim / Não / N/A)
3. **`pais`** (Padrão: BRASIL)
4. **`email`**
5. **`porte`** (ex: MICRO EMPRESA)
6. **`bairro`**
7. **`numero`**
8. **`logradouro`**
9. **`razao_social`**
10. **`nome_fantasia`**
11. **`capital_social`** (Formato numérico contábil)
12. **`ddd_telefone_1`**
13. **`ddd_telefone_2`**
14. **`opcao_pelo_mei`** (Sim / Não / N/A)
15. **`data_inicio_atividade`**
16. **`descricao_situacao_cadastral`** (ex: ATIVA)
