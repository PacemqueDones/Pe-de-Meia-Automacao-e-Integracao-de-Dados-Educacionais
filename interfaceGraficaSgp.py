import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import cadastroAPI 
import alteracaoAPI
from json import load
import pandas as pd
from datetime import date
import sgpAPI


# Configuração inicial da página
st.set_page_config(page_title="API Pé de Meia",layout="wide")

# Dicionário para seleção de meses
MESES = {
    'JANEIRO': '01 - Janeiro', 'FEVEREIRO': '02 - Fevereiro', 'MARÇO': '03 - Março',
    'ABRIL': '04 - Abril', 'MAIO': '05 - Maio', 'JUNHO': '06 - Junho',
    'JULHO': '07 - Julho', 'AGOSTO': '08 - Agosto', 'SETEMBRO': '09 - Setembro',
    'OUTUBRO': '10 - Outubro', 'NOVEMBRO': '11 - Novembro', 'DEZEMBRO': '12 - Dezembro'
}

# Função para requisitar dados da API
@st.cache_data
def requisitaCadastro(mes, mes_nome):
    return cadastroAPI.cadastroAPI(
        url='https://api-cmde.api.pedemeia-dev.nees.ufal.br/v1/estudantes?page={}&per_page=5000&situacao_matricula=ATIVAS',
        MES=mes, Mes=mes_nome, credenciaisPath='credenciais.desenvolvimento.txt'
    )

@st.cache_data
def requisitaUpdate(mes, mes_nome):
    return alteracaoAPI.alteracaoAPI(
        url='https://api-cmde.api.pedemeia-dev.nees.ufal.br/v1/estudantes?page={}&per_page=5000&situacao_matricula=ATIVAS',
        MES=mes, Mes=mes_nome, credenciaisPath='credenciais.desenvolvimento.txt'
    )

def exibir_tabela(df):
    # Configuração das opções da tabela
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(enabled=True, paginationPageSize=5)  # Paginação habilitada
    gb.configure_default_column(editable=False, resizable=True)  # Colunas ajustáveis
    gb.configure_grid_options(domLayout='normal')  # Layout fluido

    grid_options = gb.build()

    # Exibindo a tabela interativa
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        enable_enterprise_modules=False,
        height=400,
        theme='streamlit'  # Opções: "streamlit", "light", "dark", "blue", "fresh"
    )

    return grid_response

    # Exibe o DataFrame fatiado
    start_idx = (st.session_state['page'] - 1) * st.session_state['rows_per_page']
    end_idx = start_idx + st.session_state['rows_per_page']
    st.write(df.iloc[start_idx:end_idx])
    st.write(f"Número total de estudantes: {len(df)}")

def exibir_botao_download(df, mes, nome):
    st.download_button(
        label="Download base: CSV",
        data=df.to_csv(index=False, sep=';'),
        file_name=f'{mes}-{nome}_ESTUDANTES-{date.today()}.csv',
        mime='text/csv'
    )

def mostrar_dados(dados, nome):
    st.session_state['df'] = pd.DataFrame(dados)

    if 'rows_per_page' not in st.session_state:
        st.session_state['rows_per_page'] = 5
    if 'page' not in st.session_state:
        st.session_state['page'] = 1

    exibir_tabela(st.session_state['df'])
    exibir_botao_download(st.session_state['df'], st.session_state['MES'], nome)

st.title("Pé de Meia: Espírito Santo")
st.header('Seja bem-vindo ao aplicativo do Pé de Meia')
st.write("Aqui você poderá realizar todo o fluxo do programa")

st.session_state['MES'] = st.selectbox('Mês de referência', MESES.keys() )
st.divider()
st.session_state['numMes'] = MESES[st.session_state['MES']]

st.sidebar.title("Menu de Navegação")
st.sidebar.subheader('Escolha uma página')

if 'abaAtiva' not in st.session_state:
    st.session_state.abaAtiva = 'Cadastro'

with st.sidebar:
    st.button('Cadastro', on_click=lambda: setattr(st.session_state, 'abaAtiva', 'Cadastro'))
    st.button('Alteração', on_click=lambda: setattr(st.session_state, 'abaAtiva', 'Alteração'))
    st.button('Movimentação', on_click=lambda: setattr(st.session_state, 'abaAtiva', 'Movimentação'))
    st.button('Frequência', on_click=lambda: setattr(st.session_state, 'abaAtiva', 'Frequência'))

if 'botao_cadastro_clicado' not in st.session_state:
    st.session_state['botao_cadastro_clicado'] = False
if 'botao_alteracao_clicado' not in st.session_state:
    st.session_state['botao_alteracao_clicado'] = False

if st.session_state['abaAtiva'] == 'Cadastro':
    st.session_state['botao_alteracao_clicado'] = False
    acaoNome = st.session_state['abaAtiva']
    st.subheader("Cadastro")
    vertL, vertM, vertR = st.columns([0.15,0.7,0.15])
    with vertL:
        if st.button('Requisitar Dados'):
            st.session_state['botao_cadastro_clicado'] = True 
            st.session_state['dados'] = requisitaCadastro(st.session_state['MES'], st.session_state['numMes'])
            with vertM:
                if st.session_state.get('botao_cadastro_clicado', False):
                    mostrar_dados(st.session_state['dados'], acaoNome)
            with vertR:
                if st.button('Cadastrar estudantes'):
                    try:
                        url = 'https://api-cmde.api.pedemeia-dev.nees.ufal.br/v1/estudantes/lote'
                        devolutiva = sgpAPI.postAPI(url, st.session_state['data'], credenciaisPath='credenciais.desenvolvimento.txt')
                        st.write(devolutiva)
                    except Exception as e:
                        st.error(f"Erro ao cadastrar estudantes: {e}")

if st.session_state['abaAtiva'] == 'Alteração':
    st.session_state['botao_cadastro_clicado'] = False
    acaoNome = st.session_state['abaAtiva']
    st.subheader("Alteração")
    vertL, vertM, vertR = st.columns([0.15,0.7,0.15])
    with vertL:
        if st.button('Requisitar Dados'):
            st.session_state['botao_alteracao_clicado'] = True
            st.session_state['dados'] = requisitaUpdate(st.session_state['MES'], st.session_state['numMes'])
            with vertM:
                if st.session_state.get('botao_alteracao_clicado', False):
                    mostrar_dados(st.session_state['dados'], acaoNome) 

if st.session_state['abaAtiva'] == 'Movimentação':
    st.write('Conteúdo da aba Movimentação')

if st.session_state['abaAtiva'] == 'Frequência':
    st.write('Conteúdo da aba Frequência')
