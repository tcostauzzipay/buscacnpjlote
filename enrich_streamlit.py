import streamlit as st
import pandas as pd
import requests
import time
import re
import io
import csv

st.set_page_config(
    page_title="Enriquecedor de CNPJs - BrasilAPI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* CSS variables and global styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Elegant Header Card */
    .header-card {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border-left: 6px solid #4facfe;
    }
    
    .header-card h1 {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        margin: 0 0 0.5rem 0 !important;
        letter-spacing: -0.5px;
    }
    
    .header-card p {
        color: #a0aec0 !important;
        font-size: 1.05rem !important;
        margin: 0 !important;
        font-weight: 400;
    }

    /* Premium Metric Box */
    .metric-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .metric-card {
        background: #ffffff;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 4px solid #3182ce;
        flex: 1;
        min-width: 200px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
    }

    .metric-label {
        font-size: 0.85rem;
        color: #718096;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .metric-val {
        font-size: 1.8rem;
        color: #2d3748;
        font-weight: 700;
        margin-top: 0.25rem;
    }
    
    /* Table preview styling */
    .table-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        background: white;
        padding: 1rem;
        margin-top: 1rem;
    }

    /* Styling of custom tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f7fafc;
        border: 1px solid #e2e8f0;
        border-bottom: none;
        border-radius: 8px 8px 0px 0px;
        padding: 12px 24px;
        font-weight: 600;
        color: #4a5568;
        transition: all 0.3s;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #edf2f7;
        color: #2b6cb0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        border-top: 3px solid #3182ce !important;
        color: #2b6cb0 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-card">
    <h1>💼 Consulta e Enriquecimento de CNPJs</h1>
    <p>Insira uma lista de CNPJs via upload de arquivo ou cole diretamente para consultar dados completos de forma automática pela BrasilAPI.</p>
    <p style="color: #a0aec0 !important; font-size: 0.92rem !important; margin-top: 0.75rem !important; font-weight: 500;">
        ⚠️ <b>Instruções & Regras:</b> O processamento está limitado a no máximo <b>200 CNPJs por consulta</b>. As configurações de delay e rate-limiting na barra lateral foram bloqueadas para garantir a estabilidade da API e evitar sobrecargas.
    </p>
</div>
""", unsafe_allow_html=True)

if 'processed_df' not in st.session_state:
    st.session_state.processed_df = None
if 'enriching' not in st.session_state:
    st.session_state.enriching = False
if 'stop_enrichment' not in st.session_state:
    st.session_state.stop_enrichment = False

st.sidebar.markdown("### ⚙️ Configurações da API")

delay_between_requests = st.sidebar.slider(
    "Delay entre requisições (segundos) [BLOQUEADO]", 
    min_value=0.0, 
    max_value=2.0, 
    value=0.2, 
    step=0.1,
    disabled=True,
    help="Intervalo para evitar bloqueio por excesso de requisições rápidas."
)

batch_size_pause = st.sidebar.number_input(
    "Pausa a cada N consultas [BLOQUEADO]", 
    min_value=10, 
    max_value=1000, 
    value=100, 
    step=10,
    disabled=True,
    help="Após esse lote de requisições, o script fará uma pausa maior."
)

pause_duration = st.sidebar.slider(
    "Duração da pausa maior (segundos) [BLOQUEADO]", 
    min_value=1, 
    max_value=30, 
    value=5, 
    step=1,
    disabled=True,
    help="Tempo de espera após atingir o lote especificado acima."
)

retry_429_delay = st.sidebar.number_input(
    "Espera em caso de bloqueio/Rate Limit (segundos) [BLOQUEADO]", 
    min_value=5, 
    max_value=120, 
    value=30, 
    step=5,
    disabled=True,
    help="Tempo para aguardar se receber o status 429 (Too Many Requests) antes de tentar novamente."
)

target_columns_options = [
    'cnpj', 'opcao_pelo_simples', 'pais', 'email', 'porte', 'bairro', 'numero', 'logradouro',
    'razao_social', 'nome_fantasia', 'capital_social', 'ddd_telefone_1',
    'ddd_telefone_2', 'opcao_pelo_mei',
    'data_inicio_atividade', 'descricao_situacao_cadastral'
]

extra_columns_options = [
    'uf', 'municipio', 'cep', 'complemento', 'cnae_fiscal', 'cnae_fiscal_descricao'
]

st.sidebar.markdown("### 📋 Colunas para Enriquecimento")
selected_columns = st.sidebar.multiselect(
    "Selecione as colunas de retorno:",
    options=target_columns_options + extra_columns_options,
    default=target_columns_options,
    help="Selecione quais dados você deseja trazer no resultado final."
)

def clean_cnpj(val):
    if not isinstance(val, str):
        val = str(val) if pd.notna(val) else ""
    cleaned = re.sub(r'\D', '', val)
    if 0 < len(cleaned) < 14:
        cleaned = cleaned.zfill(14)
    return cleaned

def extract_cnpjs_from_text(text):
    if not text:
        return []
    cnpj_pattern = re.compile(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b|\b\d{14}\b')
    matches = cnpj_pattern.findall(text)
    cnpjs = []
    for match in matches:
        cleaned = clean_cnpj(match)
        if len(cleaned) == 14:
            cnpjs.append(cleaned)
            
    if not cnpjs:
        tokens = re.split(r'[\s,;\n\t\xa0]+', text)
        for token in tokens:
            cleaned = clean_cnpj(token)
            if len(cleaned) == 14:
                cnpjs.append(cleaned)
                
    return list(dict.fromkeys(cnpjs))

def map_brasilapi_response(data, cols):
    def format_boolean(val):
        if val is True or val == "true" or val == "True":
            return "Sim"
        if val is False or val == "false" or val == "False":
            return "Não"
        return "N/A"

    mapping = {
        'cnpj': data.get('cnpj', ''),
        'pais': str(data.get('nome_pais') or 'BRASIL').upper(),
        'email': data.get('email', '') or '',
        'porte': data.get('porte', '') or '',
        'bairro': data.get('bairro', '') or '',
        'numero': data.get('numero', '') or '',
        'logradouro': data.get('logradouro', '') or '',
        'razao_social': data.get('razao_social', '') or '',
        'nome_fantasia': data.get('nome_fantasia', '') or '',
        'capital_social': data.get('capital_social', 0.0),
        'ddd_telefone_1': data.get('ddd_telefone_1', '') or '',
        'ddd_telefone_2': data.get('ddd_telefone_2', '') or '',
        'opcao_pelo_mei': format_boolean(data.get('opcao_pelo_mei')),
        'opcao_pelo_simples': format_boolean(data.get('opcao_pelo_simples')),
        'data_inicio_atividade': data.get('data_inicio_atividade', '') or '',
        'descricao_situacao_cadastral': data.get('descricao_situacao_cadastral', '') or '',
        'uf': data.get('uf', '') or '',
        'municipio': data.get('municipio', '') or '',
        'cep': data.get('cep', '') or '',
        'complemento': data.get('complemento', '') or '',
        'cnae_fiscal': data.get('cnae_fiscal', '') or '',
        'cnae_fiscal_descricao': data.get('cnae_fiscal_descricao', '') or ''
    }
    return {col: mapping.get(col, '') for col in cols}

tab_upload, tab_paste = st.tabs(["📤 Enviar Arquivo (CSV/Excel)", "📝 Colar Lista de CNPJs"])

cnpjs_to_process = []

with tab_upload:
    st.markdown("### Envie sua planilha ou arquivo de texto")
    uploaded_file = st.file_uploader(
        "Selecione um arquivo .csv, .xlsx, .xls ou .txt contendo os CNPJs:",
        type=["csv", "xlsx", "xls", "txt"]
    )
    
    if uploaded_file is not None:
        try:
            filename = uploaded_file.name.lower()
            df_temp = None
            
            if filename.endswith(".csv"):
                try:
                    df_temp = pd.read_csv(uploaded_file, dtype=str, sep=';')
                except Exception:
                    uploaded_file.seek(0)
                    df_temp = pd.read_csv(uploaded_file, dtype=str, sep=',')
                    
            elif filename.endswith((".xlsx", ".xls")):
                df_temp = pd.read_excel(uploaded_file, dtype=str)
            else:  # TXT file
                content = uploaded_file.read().decode('utf-8-sig', errors='ignore')
                cnpjs_to_process = extract_cnpjs_from_text(content)
            
            if df_temp is not None:
                st.write("📋 **Visualização do arquivo carregado:**")
                st.dataframe(df_temp.head(5), use_container_width=True)
                
                cols = list(df_temp.columns)
                default_col_idx = 0
                for i, col in enumerate(cols):
                    if 'cnpj' in col.lower() or 'cadastro' in col.lower():
                        default_col_idx = i
                        break
                        
                cnpj_col = st.selectbox(
                    "Selecione a coluna que contém os CNPJs:",
                    options=cols,
                    index=default_col_idx
                )
                
                raw_list = df_temp[cnpj_col].dropna().tolist()
                cleaned_list = [clean_cnpj(x) for x in raw_list]
                cnpjs_to_process = list(dict.fromkeys([x for x in cleaned_list if len(x) == 14]))
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

with tab_paste:
    st.markdown("### Cole a lista de CNPJs abaixo")
    pasted_text = st.text_area(
        "Cole aqui os CNPJs (um por linha, separados por vírgula, ponto e vírgula, espaços ou mesmo formatados):",
        placeholder="10.385.218/0001-65\n10473109000108\n10.692.111/0001-60; 10742083000148",
        height=200
    )
    if pasted_text:
        cnpjs_to_process = extract_cnpjs_from_text(pasted_text)

if cnpjs_to_process:
    total_found = len(cnpjs_to_process)
    start_btn = False
    
    if total_found > 200:
        st.error(f"⚠️ **Limite de Processamento Excedido!** Sua lista contém **{total_found}** CNPJs únicos. O limite máximo permitido é de **200** CNPJs por vez para evitar bloqueios ou sobrecargas. Por favor, reduza sua lista.")
        if st.button("❌ Limpar Seleção", use_container_width=True):
            st.session_state.processed_df = None
            st.rerun()
    else:
        st.info(f"🔍 Encontrados **{total_found}** CNPJs únicos prontos para consulta.")
        
        col_btn_start, col_btn_clear = st.columns([1, 4])
        
        with col_btn_start:
            start_btn = st.button("🚀 Iniciar Enriquecimento", type="primary", use_container_width=True)
        with col_btn_clear:
            if st.button("❌ Limpar Seleção", use_container_width=True):
                st.session_state.processed_df = None
                st.rerun()

    if start_btn:
        st.session_state.enriching = True
        st.session_state.stop_enrichment = False
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        error_logs = st.empty()
        
        stop_placeholder = st.empty()
        
        enriched_data = []
        total_cnpjs = len(cnpjs_to_process)
        
        success_count = 0
        not_found_count = 0
        error_count = 0
        
        start_time = time.time()
        
        for idx, cnpj in enumerate(cnpjs_to_process):
            if st.session_state.stop_enrichment:
                st.warning("⚠️ Processo interrompido pelo usuário. Exibindo resultados parciais...")
                break
                
            percent_complete = int((idx / total_cnpjs) * 100)
            progress_bar.progress(percent_complete)
            
            if stop_placeholder.button("🛑 Parar Processamento", key=f"stop_{idx}"):
                st.session_state.stop_enrichment = True
                st.warning("Parando na próxima requisição...")
                
            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / (idx + 1) if idx > 0 else delay_between_requests
            est_remaining = avg_time * (total_cnpjs - (idx + 1))
            
            status_text.markdown(f"""
            **⏳ Processando CNPJ:** `{cnpj}` | **Progresso:** {idx + 1}/{total_cnpjs} ({percent_complete}%)
            *Tempo restante estimado: {int(est_remaining // 60)}m {int(est_remaining % 60)}s*
            """)
            
            url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
            
            try:
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    mapped = map_brasilapi_response(data, selected_columns)
                    enriched_data.append(mapped)
                    success_count += 1
                    
                elif response.status_code == 404:
                    not_found_count += 1
                    mapped = {col: "" for col in selected_columns}
                    mapped['cnpj'] = cnpj
                    mapped['descricao_situacao_cadastral'] = "NÃO ENCONTRADO"
                    enriched_data.append(mapped)
                    
                elif response.status_code == 429:
                    st.warning(f"⚠️ Rate limit atingido no CNPJ {cnpj}. Aguardando {retry_429_delay} segundos...")
                    time.sleep(retry_429_delay)
                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        mapped = map_brasilapi_response(data, selected_columns)
                        enriched_data.append(mapped)
                        success_count += 1
                    else:
                        error_count += 1
                        mapped = {col: "" for col in selected_columns}
                        mapped['cnpj'] = cnpj
                        mapped['descricao_situacao_cadastral'] = f"BLOQUEIO API ({response.status_code})"
                        enriched_data.append(mapped)
                else:
                    error_count += 1
                    mapped = {col: "" for col in selected_columns}
                    mapped['cnpj'] = cnpj
                    mapped['descricao_situacao_cadastral'] = f"ERRO ({response.status_code})"
                    enriched_data.append(mapped)
                    
            except Exception as e:
                error_count += 1
                mapped = {col: "" for col in selected_columns}
                mapped['cnpj'] = cnpj
                mapped['descricao_situacao_cadastral'] = f"ERRO EXCEÇÃO"
                enriched_data.append(mapped)
            
            if (idx + 1) % batch_size_pause == 0 and (idx + 1) < total_cnpjs:
                status_text.markdown(f"⏸️ **Pausa programada de {pause_duration} segundos para estabilização da API...**")
                time.sleep(pause_duration)
            else:
                time.sleep(delay_between_requests)
                
        progress_bar.progress(100)
        status_text.empty()
        stop_placeholder.empty()
        
        if enriched_data:
            st.session_state.processed_df = pd.DataFrame(enriched_data, columns=selected_columns)
            st.success("🎉 Consulta de CNPJs concluída com sucesso!")
        else:
            st.error("Nenhum CNPJ pôde ser consultado.")
            
        st.session_state.enriching = False

if st.session_state.processed_df is not None:
    df_results = st.session_state.processed_df.copy()
    
    if 'capital_social' in df_results.columns:
        df_results['capital_social'] = pd.to_numeric(df_results['capital_social'], errors='coerce').fillna(0.0)

    st.markdown("### 📊 Estatísticas do Lote")
    
    total = len(df_results)
    if total > 0:
        found_num = len(df_results[~df_results['descricao_situacao_cadastral'].isin(["NÃO ENCONTRADO", "ERRO EXCEÇÃO"]) & ~df_results['descricao_situacao_cadastral'].str.startswith("ERRO", na=False)])
        not_found_num = len(df_results[df_results['descricao_situacao_cadastral'] == "NÃO ENCONTRADO"])
        errors_num = total - found_num - not_found_num
        success_pct = (found_num / total) * 100
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card" style="border-top-color: #2b6cb0;">
                <div class="metric-label">Total Processado</div>
                <div class="metric-val">{total}</div>
            </div>
            <div class="metric-card" style="border-top-color: #48bb78;">
                <div class="metric-label">Encontrados / Válidos</div>
                <div class="metric-val">{found_num}</div>
            </div>
            <div class="metric-card" style="border-top-color: #ed8936;">
                <div class="metric-label">Não Encontrados</div>
                <div class="metric-val">{not_found_num}</div>
            </div>
            <div class="metric-card" style="border-top-color: #e53e3e;">
                <div class="metric-label">Erros / Falhas</div>
                <div class="metric-val">{errors_num}</div>
            </div>
            <div class="metric-card" style="border-top-color: #319795;">
                <div class="metric-label">Taxa de Sucesso</div>
                <div class="metric-val">{success_pct:.1f}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 🔍 Filtros Interativos")
    st.info("Utilize os filtros abaixo para restringir os dados da planilha mostrada e dos botões de exportação.")
    
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    situacao_options = ["Todos"]
    porte_options = ["Todos"]
    
    if 'descricao_situacao_cadastral' in df_results.columns:
        unique_sit = df_results['descricao_situacao_cadastral'].dropna().unique().tolist()
        situacao_options.extend([x for x in unique_sit if x])
        
    if 'porte' in df_results.columns:
        unique_porte = df_results['porte'].dropna().unique().tolist()
        porte_options.extend([x for x in unique_porte if x])

    with col1:
        f_situacao = st.selectbox("Filtrar por Situação Cadastral:", options=situacao_options)
    with col2:
        f_porte = st.selectbox("Filtrar por Porte da Empresa:", options=porte_options)
    with col3:
        f_simples = st.selectbox("Opção pelo Simples Nacional:", options=["Todos", "Sim", "Não", "N/A"])
        
    with col4:
        f_mei = st.selectbox("Opção pelo MEI:", options=["Todos", "Sim", "Não", "N/A"])
    with col5:
        f_name_search = st.text_input("Buscar por Razão Social / Nome Fantasia:", placeholder="Digite para filtrar...")
    with col6:
        f_location_search = st.text_input("Buscar por Logradouro / Bairro / UF:", placeholder="Digite rua, bairro ou estado...")

    df_filtered = df_results.copy()
    
    if f_situacao != "Todos" and 'descricao_situacao_cadastral' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['descricao_situacao_cadastral'] == f_situacao]
        
    if f_porte != "Todos" and 'porte' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['porte'] == f_porte]
        
    if f_simples != "Todos" and 'opcao_pelo_simples' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['opcao_pelo_simples'] == f_simples]
        
    if f_mei != "Todos" and 'opcao_pelo_mei' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['opcao_pelo_mei'] == f_mei]
        
    if f_name_search:
        search_mask = False
        if 'razao_social' in df_filtered.columns:
            search_mask = search_mask | df_filtered['razao_social'].str.contains(f_name_search, case=False, na=False)
        if 'nome_fantasia' in df_filtered.columns:
            search_mask = search_mask | df_filtered['nome_fantasia'].str.contains(f_name_search, case=False, na=False)
        if isinstance(search_mask, pd.Series):
            df_filtered = df_filtered[search_mask]
            
    if f_location_search:
        loc_mask = False
        for c in ['logradouro', 'bairro', 'uf', 'municipio']:
            if c in df_filtered.columns:
                loc_mask = loc_mask | df_filtered[c].str.contains(f_location_search, case=False, na=False)
        if isinstance(loc_mask, pd.Series):
            df_filtered = df_filtered[loc_mask]

    st.write(f"Showing **{len(df_filtered)}** out of **{len(df_results)}** records after filtering:")

    st.dataframe(df_filtered, use_container_width=True)

    st.markdown("### 💾 Exportar Dados")
    
    excel_buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='CNPJs Enriquecidos')
            
            workbook = writer.book
            worksheet = writer.sheets['CNPJs Enriquecidos']
            
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#1f4068',
                'font_color': '#ffffff',
                'border': 1
            })
            
            for col_num, value in enumerate(df_filtered.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            for idx, col in enumerate(df_filtered.columns):
                series = df_filtered[col]
                max_len = max((
                    series.astype(str).map(len).max(),
                    len(str(series.name))
                )) + 3
                worksheet.set_column(idx, idx, min(max_len, 50))
                
        excel_data = excel_buffer.getvalue()
    except Exception as e:
        excel_data = None
        st.sidebar.error(f"Erro ao formatar Excel: {e}")

    csv_buffer = io.StringIO()
    df_filtered.to_csv(csv_buffer, index=False, sep=';', encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    csv_data = csv_buffer.getvalue().encode('utf-8-sig')

    col_dl_csv, col_dl_xlsx = st.columns(2)
    
    with col_dl_csv:
        st.download_button(
            label="📥 Baixar Planilha em CSV (Separado por ';')",
            data=csv_data,
            file_name="cnpjs-enriquecidos.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_dl_xlsx:
        if excel_data is not None:
            st.download_button(
                label="📥 Baixar Planilha em Excel (.xlsx)",
                data=excel_data,
                file_name="cnpjs-enriquecidos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.warning("Exportação em formato Excel não está disponível.")
