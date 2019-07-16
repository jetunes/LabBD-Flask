import os
import psycopg2
from flask import current_app, g
from datetime import date

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL)


def initDB():
	print("Criando todas as tabelas...")
	with conn.cursor() as cursor:
		cursor.execute(open("schema.sql", "r").read())
	conn.commit()	
	conn.commit()
	
	
	print("Banco de Dados pronto para o uso")
	
def qtdEditais(abertos=True):
	code = "SELECT count(*) FROM vEditais_Abertos"
	if not abertos:
		code = "SELECT count(*) FROM vEditais_Fechados"
		
	with conn.cursor() as cur:
		cur.execute(code)
		dados = cur.fetchone()
		return int(dados[0])

def extra():
	curs = conn.cursor()
	curs.execute("ROLLBACK")
	conn.commit()
	
def editaisDetalhes(id_ed):
	with conn.cursor() as cur:
		cur.execute("SELECT data_abertura, data_encerramento, tipo, titulo, codigo FROM edital WHERE codigo = %s;", [id_ed])
		dado1 = cur.fetchone()
		
		cur.execute("SELECT proponente FROM proponente WHERE codigo_edital = %s;", [id_ed])
		dado2 = cur.fetchall()
		
		cur.execute("SELECT bolsa FROM bolsa WHERE codigo_edital = %s;", [id_ed])
		dado3 = cur.fetchall()
		
		cur.execute("SELECT objetivo FROM objetivo WHERE codigo_edital = %s;", [id_ed])
		dado4 = cur.fetchall()
		
		cur.execute("SELECT atividade, data FROM cronograma WHERE codigo_edital = %s;", [id_ed])
		dado5 = cur.fetchall()
		
		cur.execute("SELECT disposicao FROM disposicoes_gerais WHERE codigo_edital = %s;", [id_ed])
		dado6 = cur.fetchall()

		return dado1, dado2, dado3, dado4, dado5, dado6

def editais(pagina = 0, abertos = True):
	code = "SELECT * FROM vEditais_Abertos ORDER BY tempo_restante ASC, titulo LIMIT 15 OFFSET %s;"
	if not abertos:
		code = "SELECT * FROM vEditais_Fechados ORDER BY data_encerramento DESC, titulo LIMIT 15 OFFSET %s;"

	with conn.cursor() as cur:
		cur.execute(code, [pagina])
		dados = cur.fetchall()
		return dados
		
def checaPessoa(cpf):
	with conn.cursor() as cur:
		
		cur.execute("SELECT id_pessoa, nome FROM vCpfPassaporte WHERE cpfoupass = %s;", [cpf])
		dados = cur.fetchone()
		print(cpf, dados)
		cur.execute("SELECT count(*) FROM CoordenadorCoordenaAtividade WHERE id_pessoa = %s;", [dados[0]])
		coordena = cur.fetchone()
		cur.execute("SELECT count(*) FROM PessoaServidor WHERE id_pessoa = %s;", [dados[0]])
		servidor = cur.fetchone()
		cur.execute("SELECT count(*) FROM PessoaGraduacao WHERE id_pessoa = %s;", [dados[0]])
		graduacao = cur.fetchone()
		cur.execute("SELECT count(*) FROM PessoaPosgraduacao WHERE id_pessoa = %s;", [dados[0]])
		posgraduacao = cur.fetchone()
		return dados, coordena, servidor, graduacao, posgraduacao
		
def criaPessoa(nome, cpf, senha, estado, cidade, bairro, rua, numero, funcao, num_UFSCar, dep):
	curs = conn.cursor()
	curs.execute("ROLLBACK")
	conn.commit()

	id_novo = -1
	with conn.cursor() as cur:
		cur.execute("INSERT INTO pessoa (nome, senha, uf, cidade, bairro, rua, numero) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_pessoa;", [nome, senha, estado, cidade, bairro, rua, numero])
		#cur.execute("SELECT id_pessoa FROM Pessoa WHERE nome = %s", [nome])
		id_novo = cur.fetchone()[0]
			
		cur.execute("INSERT INTO pessoabrasileira (cpf, id_pessoa) VALUES (%s, %s);", [cpf, id_novo])
		if funcao == "Graduação":
			cur.execute("INSERT INTO PessoaGraduacao (nro_ufscar, id_pessoa) VALUES (%s, %s);", [num_UFSCar, id_novo])
		if funcao == "Pós-Graduação":
			cur.execute("INSERT INTO PessoaPosGraduacao (nro_ufscar, id_pessoa) VALUES (%s, %s);", [num_UFSCar, id_novo])
		if funcao == "Docente":
			cur.execute("INSERT INTO PessoaServidor (id_pessoa, id_departamento, nro_ufscar, data_contratacao) VALUES (%s, %s, %s, current_date);", [id_novo, dep, num_UFSCar])
			cur.execute("INSERT INTO PessoaServidorDocente (id_pessoa, id_departamento, titulo, cargo, setor, tipo) VALUES (%s, %s, %s, %s, %s, %s);", [id_novo, dep, "Senhor(a)", "Professor", "Computação", "Adjunto"])
		if funcao == "Técnico":
			cur.execute("INSERT INTO PessoaServidor (id_pessoa, id_departamento, nro_ufscar, data_contratacao) VALUES (%s, %s, %s, current_date);", [id_novo, dep, num_UFSCar])
			cur.execute("INSERT INTO PessoaServidorTecnico (id_pessoa, id_departamento) VALUES (%s, %s);", [id_novo, dep])
	conn.commit()
	return id_novo
	
def listaDep():
	cur = conn.cursor()
	cur.execute("SELECT * FROM Departamento;")
	return cur.fetchall()

def ListaAtividades(id_pessoa):
	cur = conn.cursor()
	cur.execute("SELECT * FROM vAtividades;")
	dados = cur.fetchall()
	
	resultados = []
	if id_pessoa > 0:
		for d in dados:
			cur.callproc('VerificaInscricao', [id_pessoa, d[0]])
			R = cur.fetchone()
			resultados.append([d[0], R[0]])
	return dados, resultados

# Inserida por Vitor
def atividadeComDetalhes(id_at):
	cur = conn.cursor()
	cur.execute("SELECT nro_extensao, publico_alvo, palavras_chave, resumo, inicio_real, fim_real, inicio_previsto, fim_previsto, data_aprovacao, tipo_atividade, titulo, status FROM AtividadeDeExtensao WHERE nro_extensao = %s;", [id_at])
	dado1 = cur.fetchone()

	cur.execute("SELECT nome_area FROM Area, AtividadeDeExtensao WHERE id_area = id_area_pr and nro_extensao = %s;", [id_at])
	dado2 = cur.fetchall()

	cur.execute("SELECT nome_area FROM Area, AtividadeDeExtensao WHERE id_area = id_area_se and nro_extensao = %s;", [id_at])
	dado3 = cur.fetchall()

	cur.execute("SELECT agencia FROM Financiador f, AtividadeDeExtensao a WHERE f.id_financiador = a.id_financiador and nro_extensao = %s;", [id_at])
	dado4 = cur.fetchall()

	cur.execute("SELECT a.titulo FROM ProgramaDeExtensao p, AtividadeDeExtensao a WHERE p.nro_extensao = a.nro_extensao_programa and a.nro_extensao = %s;", [id_at])
	dado5 = cur.fetchall()

	cur.execute("SELECT  nro_extensao, horario_aulas, ementa, carga_horaria_prevista FROM Aciepe WHERE nro_extensao = %s;", [id_at])
	dado6 = cur.fetchall()

	cur.execute("SELECT  nro_extensao, data, horario, local, campus FROM Aciepe_Encontros WHERE nro_extensao = %s;", [id_at])
	dado7 = cur.fetchall()
	
	

	return dado1, dado2, dado3, dado4, dado5, dado6, dado7
		
# Inserida por Vitor
def participantesInfos(id_atividade, id_part,):
	cur = conn.cursor()
	cur.execute("SELECT id_pessoa, nro_extensao, frequencia, avaliacao FROM Participante WHERE id_pessoa = %s and nro_extensao = %s;", [id_part, id_atividade]) 
	dado1 = cur.fetchone()

	cur.execute("SELECT titulo, status, resumo FROM AtividadeDeExtensao a WHERE  a.nro_extensao = %s;",[id_atividade]) 
	dado2 = cur.fetchone()

	cur.execute("SELECT nome FROM Pessoa a WHERE a.id_pessoa = %s;",[id_part]) 
	dado3 = cur.fetchone()
	
	cur.execute("SELECT P.nome, E.email FROM Pessoa P, Pessoa_Email E, CoordenadorCoordenaAtividade C WHERE P.id_pessoa = E.id_pessoa and P.id_pessoa = C.id_pessoa and C.nro_extensao = %s;", [id_atividade])
	dado4 = cur.fetchone()
	return dado1, dado2, dado3, dado4


def getInformacoes(id_pessoa):
	cur = conn.cursor()
	
	cur.execute("SELECT titulo, cargo FROM PessoaServidorDocente WHERE id_pessoa = %s;", [id_pessoa])
	tituloCargo = cur.fetchone()
	
	cur.execute("SELECT id_departamento, nro_ufscar, data_contratacao FROM PessoaServidor WHERE id_pessoa = %s;", [id_pessoa])
	iddepNroData = cur.fetchone()
	
	if iddepNroData:
		cur.execute("SELECT nome from Departamento WHERE id_departamento = %s;", [iddepNroData[0]])
		nomeDep = cur.fetchone()
	else:
		nomeDep = ['--']
	
	cur.execute("SELECT uf, cidade, bairro, rua, numero FROM Pessoa WHERE id_pessoa = %s;", [id_pessoa])
	endereco = cur.fetchone()
	
	cur.execute("SELECT email FROM Pessoa_Email WHERE id_pessoa = %s;", [id_pessoa])
	emails = cur.fetchall()
	
	cur.execute("SELECT ddi, ddd, fixo FROM Pessoa_Telefone WHERE id_pessoa = %s;", [id_pessoa])
	telefones = cur.fetchall()
	
	return tituloCargo, iddepNroData, nomeDep, endereco, emails, telefones
	
def getParticipacao(id_pessoa):
	cur = conn.cursor()
	
	cur.execute("SELECT P.titulo, S.id_selecao, S.declaracao_presenca, S.selecionado FROM Participante_participa_Selecao S, ProgramaDeExtensao P WHERE id_pessoa = %s and P.nro_extensao = S.nro_extensao;", [id_pessoa])
	selecao = cur.fetchall()
	
	cur.execute("SELECT P.titulo, P.nro_extensao FROM Participante Part, ProgramaDeExtensao P WHERE Part.id_pessoa = %s and P.nro_extensao = Part.nro_extensao;", [id_pessoa])
	participacao = cur.fetchall()
	return selecao, participacao

def inscreverAtividade(id_pessoa, id_atividade):
	cur = conn.cursor()
	cur.execute("INSERT INTO Participante (id_pessoa, nro_extensao, frequencia, avaliacao) VALUES (%s,  %s, null, null);", [id_pessoa, id_atividade])
	conn.commit()

def getServidor(id_pessoa):
	cur = conn.cursor()
	
	cur.execute("SELECT E.titulo, E.tipo, E.data_abertura, E.data_encerramento , E.codigo FROM edital E WHERE E.data_encerramento > %s;", [date.today()])
	editais_abertos = cur.fetchall()
	
	return editais_abertos


def criaProposta(id_pessoa, areatematica_grandearea, areatematica_areasecundaria, areatematica_areaprincipal, resumo, descricao, setor_responsavel, abrangencia, comunidade_atingida, publico_alvo, DataInicio, DataFim, id_edital, tipo):
	curs = conn.cursor()
	curs.execute("ROLLBACK")
	conn.commit()

	cur.execute("SELECT id_departamento, nro_ufscar, data_contratacao FROM PessoaServidor WHERE id_pessoa = %s;", [id_pessoa])
	iddepNroData = cur.fetchone()
	
	id_novo = -1
	with conn.cursor() as cur:
		cur.execute("INSERT INTO Proposta (status, id_pessoa, id_departamento, codigo_edital, nro_processo, tipo, areatematica_grandearea, areatematica_areasecundaria, areatematica_areaprincipal, resumo, comunidade_atingida, publico_alvo, DataFim, DataInicio, descricao, setor_responsavel, abrangencia) VALUES ('em andamento', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id_proposta;", [id_pessoa, iddepNroData[0], id_pessoa, id_pessoa, tipo, areatematica_grandearea, areatematica_areasecundaria, areatematica_areaprincipal, resumo, comunidade_atingida, publico_alvo, DataFim, DataInicio, descricao, setor_responsavel, abrangencia])
		#cur.execute("SELECT id_pessoa FROM Pessoa WHERE nome = %s", [nome])
		id_novo = cur.fetchone()[0]
	conn.commit()
	return id_novo