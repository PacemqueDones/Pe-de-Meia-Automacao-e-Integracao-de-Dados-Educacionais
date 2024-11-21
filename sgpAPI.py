from requests import get, post, patch
from json import loads, dump
from pandas import read_csv, isna, to_numeric, to_datetime, notna
from os.path import join, splitext
from os import listdir
from chardet import detect
from csv import Sniffer
from datetime import date, datetime

def readCrenciais(credenciaisPath='credenciais.producao.txt'):
	with open(credenciaisPath) as file:
	    credenciais = file.read().replace("'",'"')
	    credenciais = loads(credenciais)
	return credenciais

def matriculaAtiva(row):
    if (row['situacao_matricula'] == 'Em curso') and (isna(row['data_encerramento_matricula'])) \
    and (row['situacao_enturmacao'] == 'Em curso') and (isna(row['data_saida'])) \
    and (isna(row['situacao_final'])):
        return True
    else:
        return False

def idade(row):
	hoje = date.today()
	if (hoje.month,hoje.day) < (row.month,row.day):
		return ((hoje.year - row.year) - 1)
	else:
		return (hoje.year - row.year)

def writeJson(nomeFile, data):
	with open(f'{nomeFile}.json', 'w') as file:
		dump(data, file)

def readBase(caminhoBase, **arg):
	with open(caminhoBase, 'rb') as file:
		data = file.read(4096)
		result = detect(data)
		encoding = result['encoding']
	with open(caminhoBase, 'r', newline='', encoding=encoding)  as file:
		sample = file.read(16384)
		sniffer = Sniffer()
		dialect = sniffer.sniff(sample)
		delimiter = dialect.delimiter
	return read_csv(caminhoBase, sep=delimiter, encoding=encoding, **arg)

nextPage=1
activeRegistration=[]

def getAPI(url, nomeFile, credenciaisPath='credenciais.producao.txt'):
	global nextPage
	global activeRegistration
    
	credenciais = readCrenciais(credenciaisPath)
	
	while nextPage is not None:
		response = get(
			url=url.format(nextPage),
			headers=credenciais['headers'],
			proxies=credenciais['proxies']
		)
		if response.status_code == 200:
			data = response.json()
			activeRegistration += data['data']
			print(f'Status_code: {response.status_code},{nextPage}, {len(activeRegistration)}')
            
		else:
			print(f'Erro na requisição: {response.status_code}')
        
		nextPage = data['pagination']['links']['next']
		
	writeJson(nomeFile=nomeFile, data=activeRegistration)
		
	return activeRegistration

def postAPI(url, data, credenciaisPath='credenciais.producao.txt'):
	credenciais = readCrenciais(credenciaisPath)
	
	response = post(
		url=url,
	    headers=credenciais['headers'],
	    proxies=credenciais['proxies'],
	    json=data
	)
	if response.status_code == 200:
		data = response.json()
		activeRegistration += data['data']
		print(f'Status_code: {response.status_code},{nextPage}, {len(activeRegistration)}')
		return response.json()
	else:
		print(f'Erro na requisição: {response.status_code}')

def patchAPI(url, data, credenciaisPath='credenciais.producao.txt'):
	credenciais = readCrenciais(credenciaisPath)
	
	response = patch(
		url=url,
	    headers=credenciais['headers'],
	    proxies=credenciais['proxies'],
	    json=data
	)
	if response.status_code == 200:
		data = response.json()
		activeRegistration += data['data']
		print(f'Status_code: {response.status_code},{nextPage}, {len(activeRegistration)}')
		return response.json()
	else:
		print(f'Erro na requisição: {response.status_code}') 

def baseSegesLimpa(pastaMes):
	Data_Base = fr'N:/04 - Relatórios/Relatórios SGE/13 - Relatórios JIRA/03- Relatórios jiras base de alunos semanal/2024/{pastaMes}'
	Data_Folder = join(Data_Base,'ALUNO')

	arquivos = listdir(Data_Folder)

	arquivos = [file for file in arquivos if splitext(file)[1] == '.csv']
	
	dataFile = max( map( lambda x: (datetime.strptime(x[-14:28], '%d_%m_%Y').date(), x), arquivos ), key= lambda x: x[0] )[1]

	dfBasal = readBase(f'{Data_Folder}\\{dataFile}',dtype={1:str})

	dfBasal['cpf'] = dfBasal['cpf'].str.replace('.','',regex=False).str.replace('-','',regex=False)

	dfBasal['cpf'] = to_numeric(dfBasal['cpf'],errors='coerce')

	dfBasal['cpf'] = dfBasal['cpf'].astype(str).apply(lambda x: None if x=='nan' else x)
	
	dfBasal['cpf'] = dfBasal['cpf'].apply(lambda x: "{:.0f}".format(float(x)) if notna(x)  else x)

	dfBasal['cpf'] = dfBasal['cpf'].str.zfill(11)
	
	dfBasal['nis'] = dfBasal['nis'].str.replace('.','',regex=False).str.replace('-','',regex=False)
	
	dfBasal['nis'] = to_numeric(dfBasal['nis'],errors='coerce')

	dfBasal['nis'] = dfBasal['nis'].astype(str).apply(lambda x: None if x=='nan' else x)
	
	dfBasal['nis'] = dfBasal['nis'].apply(lambda x: "{:.0f}".format(float(x)) if notna(x)  else x)

	dfBasal['nis'] = dfBasal['nis'].str.zfill(11)
	
	dfBasal['cpf_respons'] = dfBasal['cpf_respons'].str.replace('.','',regex=False).str.replace('-','',regex=False)
	
	dfBasal['cpf_respons'] = to_numeric(dfBasal['cpf_respons'],errors='coerce')

	dfBasal['cpf_respons'] = dfBasal['cpf_respons'].astype(str).apply(lambda x: None if x=='nan' else x)
	
	dfBasal['cpf_respons'] = dfBasal['cpf_respons'].apply(lambda x: "{:.0f}".format(float(x)) if notna(x)  else x)

	dfBasal['cpf_respons'] = dfBasal['cpf_respons'].str.zfill(11)

	dfBasal = dfBasal[dfBasal['tipo_atendimento'] == 'Regular']

	dfBasal['numero_ano_escolaridade'] = dfBasal['nome_ano_escolaridade'].apply(lambda x : x[:2] if isinstance(x, str) else x)
	
	dfBasal['numero_ano_escolaridade'] = dfBasal['numero_ano_escolaridade'].astype(int)

	dfBasal.data_nascimento = to_datetime(dfBasal.data_nascimento,format="%Y-%m-%d")
	
	dfBasal['idade'] = dfBasal.data_nascimento.apply(idade)
	
	dfBasal['data_nascimento'] = dfBasal.data_nascimento.dt.strftime('%Y-%m-%d')

	dfSeges = dfBasal

	dfSeges = dfSeges[dfSeges.num_ano_letivo.isin(['2024','2024 - 2/S', '2024 - IASES', '2024/2S - IASES', '2024 - UP',
	                                               '2024/2S - UP', '2024 - MEPES', '2024/2S - MEPES'])]
	
	dfSeges = dfSeges[dfSeges.apply(matriculaAtiva, axis=1)]
	
	dfSeges = dfSeges[(dfSeges['idade'] >= 14) & (dfSeges['idade'] <= 24)]

	dfSeges = dfSeges[dfSeges['numero_ano_escolaridade'].isin([25,26,27,28,29,30,31,32,33,34,35,36,37,38,45,48,62,63,67,71,74])]

	return dfSeges

def baseTransporteLimpa(transportData):

    arquivos = listdir(transportData)
	
    arquivos = [file for file in arquivos if splitext(file)[1] == '.csv']
	
    transportFile = max( map( lambda x: (datetime.strptime(x[-14:30], '%d_%m_%Y').date(), x), arquivos ), key= lambda x: x[0] )[1]
	
    dfTransporte = readBase(f'{transportData}\\{transportFile}',dtype={1:str})
	
    dfIbge = readBase(r'N:\04 - Relatórios\Relatórios SGE\13 - Relatórios JIRA\Código_ibge_estado_municipio.csv')
	
    ibgeEstado = dfIbge.set_index('nm_uf')['cod_uf'].to_dict()
	
    dfTransporte = dfTransporte.drop_duplicates(subset='id_aluno', keep='last')\
	    [['id_aluno','endereco','numero','complemento', 'bairro', 'municipioaluno','distrito', 'uf']]
	
    dfTransporte = dfTransporte.dropna(how='all',subset=['endereco','numero','complemento', 'bairro', 'municipioaluno', 'uf'])
	
    dfTransporte['numero'] = dfTransporte.numero.astype(str).apply(lambda x: '00' if not x.isdigit() else x)

    dfTransporte = dfTransporte.rename(columns={'uf':'nm_uf','municipioaluno':'nm_municipio'})
	
    dfTransporte['cod_uf']=dfTransporte.nm_uf.map(ibgeEstado)
	
    dfTransporte['id_aluno'] = dfTransporte.id_aluno.astype(int)
	
    dfTransporte = dfTransporte.merge(dfIbge[['cod_uf','nm_municipio','ibge_municipio']], on=['cod_uf','nm_municipio'])

    dfTransporte = dfTransporte.drop(columns=['nm_municipio','nm_uf'])

    dfTransporte['cod_uf'] = dfTransporte.cod_uf.astype(str)

    dfTransporte['ibge_municipio'] = dfTransporte.ibge_municipio.astype(str)

    return dfTransporte

def genero(row):
    if row == 'Masculino':
        return '1'
    elif row == 'Feminino':
        return '2'
    else:
        return '0'

def racaCor(row):
	if row == 'Não declarada':
		return '0'
	if row == 'Branca':
		return '1'
	if row == 'Preta':
		return '2'
	if row == 'Parda':
		return '3'
	if row == 'Indígena':
		return '4'
	if row == 'Amarela':
		return '5'

def turmaOrganizacaoQuantidadeTotal(row):
	if row == 67:
		return '4'
	else:
		return '3'

def formaOrganizacaoTurma(row):
	if (row == '2024') or (row == '2024 - IASES') or (row == '2024 - UP') or (row == '2024 - MEPES'):
		return '1'
	elif (row == '2024 - 2/S') or (row == '2024/2S - IASES') or (row == '2024/2S - UP') or (row == '2024/2S - MEPES'):
		return '2'

def estudanteEjaAnoPeriodo(row):
	if row == '1ª ETAPA':
		return '1'
	elif row == '2ª ETAPA':
		return '2'
	elif row == '3ª ETAPA':
		return '3'
	elif row == '4ª ETAPA':
		return '3'

def dataInicioPeriodoLetivo(row):
	if row == '2024' or row == '2024 - IASES' or row == '2024 - UP' or '2024 - MEPES':
		return '2024-02-05'
	elif row == '2024 - 2/S' or row == '2024/2S - IASES' or row == '2024/2S - UP' or '2024/2S - MEPES':
		return '2024-07-25'

def estudantePpl(row):
	if row == 'Unidade de educação socioeducativa':
		return '1'
	elif row == 'Unidade Prisional':
		return '2'
	else:
		return '0'

def estudanteIntegral(row):
	if (row == 'INTEGRAL 7H-TARDE') or (row == 'INTEGRAL 7H-MANHA') or (row == 'INTEGRAL') or (row == 'INTEGRAL 9H30MIN') or (row == 'INTEGRAL 8H'):
		return '1'
	else:
		return '0'

def inserirColunas(dfSeges):
	dfSeges.genero = dfSeges.genero.apply(genero)
	
	dfSeges.racaCor = dfSeges.racaCor.apply(racaCor)	 
	
	dfSeges['turmaOrganizacaoQuantidadeTotal'] = dfSeges.serieAno.apply(turmaOrganizacaoQuantidadeTotal)
	
	dfSeges['formaOrganizacaoTurma'] = dfSeges.num_ano_letivo.apply(formaOrganizacaoTurma)
	
	dfSeges.ano_escolaridade = dfSeges.ano_escolaridade.str[:8].str.replace('º','ª')
	
	dfSeges['estudanteEjaAnoPeriodo'] = dfSeges.ano_escolaridade.apply(estudanteEjaAnoPeriodo)
	
	dfSeges['dataInicioPeriodoLetivo'] = dfSeges.num_ano_letivo.apply(dataInicioPeriodoLetivo)
	
	dfSeges['estudantePpl'] = dfSeges.local_funcionamento_diferenciado.apply(estudantePpl)
	
	dfSeges['estudanteIntegral'] = dfSeges.dc_turno.apply(estudanteIntegral)

	return dfSeges

def putFilter(dfSeges):
	filtro = ["cpfResponsavel","nomeMaeEstudante",
	    "cpf","nome","dataNascimento","genero","racaCor","email","telefone",
	    "numeroNIS","logradouro","bairro","numero",
	    "municipio","uf","estudantePpl","dataInicioMatricula",
	    "serieAno","matriculaRede","inep","dataInicioPeriodoLetivo",
	    "formaOrganizacaoTurma","turmaOrganizacaoQuantidadeTotal",
	    "estudanteEjaAnoPeriodo","estudanteIntegral"]

	dfSeges = dfSeges[filtro]

	return dfSeges

def comparaBases(dfSeges, activeRegistration):
	jsonSeges = dfSeges.to_json(orient='table')
	
	jsonSeges = loads(jsonSeges)
	
	jsonSeges = jsonSeges['data']

	for infStuent in jsonSeges:
	    infStuent.pop('index', None)
		
	for data in jsonSeges:
		insertCpfNis(data)

	for data in activeRegistration:
		insertCpfNis(data)

	cpfNisSGPStudent = {SGPStudent['cpfNis'] for SGPStudent in activeRegistration}

	registerStudent = []
	for SegesStudent in jsonSeges:
	    if SegesStudent['cpfNis']!=None and SegesStudent['cpfNis'] not in cpfNisSGPStudent:
	        registerStudent.append(SegesStudent)
	
	return registerStudent

def insertCpfNis(data):
    if data['cpf'] == None:
        data['cpfNis'] = data['numeroNIS'] 
    elif data['numeroNIS'] == None:
        data['cpfNis'] = data['cpf']
    else:
        data['cpfNis'] = data['cpf']

def padronizarDicionário(dicionario):
    chaves =[
        'cpf','numeroNIS','logradouro','bairro',
        'numero','municipio','uf','cpfResponsavel',
        'genero','racaCor', 'email','telefone',
        'nomeMaeEstudante','dataNascimento','nome',
        'cpfNis'
    ]
    
    return {chave: dicionario[chave] for chave in chaves }
		
def registrationUpdate(jsonSeges,activeRegistration):
    for data in jsonSeges:
        insertCpfNis(data)

    for data in activeRegistration:
        insertCpfNis(data)

    activeRegistration = list(map(padronizarDicionário, activeRegistration))
		
    jsonSeges = list(map(padronizarDicionário, jsonSeges))
		
    cpfNisSgp = {student['cpfNis'] for student in activeRegistration}

    cpfNisSeges = {student['cpfNis'] for student in jsonSeges}

    commonCpfNis = cpfNisSgp.intersection(cpfNisSeges)

    activeRegisDict = {stuDict['cpfNis']: stuDict for stuDict in activeRegistration}

    jsonSegesDict = {stuDict['cpfNis']: stuDict for stuDict in jsonSeges}

    registrationUpdate = []
    for identifier in commonCpfNis:
        if activeRegisDict[identifier] != jsonSegesDict[identifier]:
            registrationUpdate.append(jsonSegesDict[identifier])

    return registrationUpdate