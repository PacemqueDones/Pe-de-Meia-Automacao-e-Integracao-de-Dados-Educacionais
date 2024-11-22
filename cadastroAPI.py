from json import load
from  pandas import read_csv
from datetime import datetime, date
import sgpAPI
import downloadBase

def cadastroAPI(
    url = 'https://api-cmde.api.pedemeia-dev.nees.ufal.br/v1/estudantes?page={}&per_page=5000&situacao_matricula=ATIVAS',
    MES = 'SETEMBRO',
    Mes = '09 - Setembro',
	credenciaisPath='credenciais.desenvolvimento.txt'):
    ### Getting Student

    try:
        with open(f'Alunos_Ativos_SGP_{datetime.today().date()}.json', 'r') as file:
            activeRegistration = load(file)
    except:
        activeRegistration= sgpAPI.getAPI(url, credenciaisPath=credenciaisPath, nomeFile= f'Alunos_Ativos_SGP_{datetime.today().date()}')
    
    ### Base aluno SEGES
    
    dfSeges = sgpAPI.baseSegesLimpa(Mes)
    
    relatorio = downloadBase.BaixarRelatorio(tipoBase = 'TRANSPORTE', credenciaisPath='credenciais.producao.txt')
	
    relatorio.configurar_diretorios()

    dfTransporte = sgpAPI.baseTransporteLimpa(relatorio.downloadFolder)
    
    dfSeges = dfSeges.merge(dfTransporte, on='id_aluno', how='left')
    
    dfSeges = dfSeges.rename(columns={
        'cpf_respons':'cpfResponsavel', 'nm_filiacao_1':'nomeMaeEstudante',
        'nm_aluno':'nome', 'data_nascimento':'dataNascimento',
        'dc_sexo':'genero', 'dc_cor_raca':'racaCor',
        'email_aluno':'email', 'telefones_aluno':'telefone',
        'nis':'numeroNIS', 'numero_ano_escolaridade':'serieAno',
		'dt_enturmacao':'dataInicioMatricula', 'id_aluno':'matriculaRede',
		'inep_escola':'inep', 'endereco':'logradouro',
		'ibge_municipio':'municipio', 'cod_uf':'uf'
    })
    
    dfSeges = sgpAPI.inserirColunas(dfSeges)
    
    dfSeges = sgpAPI.putFilter(dfSeges)

    return sgpAPI.comparaBases(dfSeges, activeRegistration)
