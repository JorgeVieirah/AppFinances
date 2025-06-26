from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'chave_secreta'
DATABASE = 'gastos.db'

# verifica se ja existe uma 
def get_db():
    if 'db' not in g: #verifica se tem ou não uma conexão cm o bd guardada na variavel
        g.db = sqlite3.connect(DATABASE) #cria uma conexão
        g.db.row_factory = sqlite3.Row #converte os resultados em nomes (tip dicionario)
    return g.db #retorna a conexão

@app.teardown_appcontext #qunao terminar a requisição executa a def
def close_db(error):
    db = g.pop('db', None) #tenta pegar e remover a conexão cm o bd da variavel
    if db is not None:
        db.close() #fecha a conexão corretamente

# funcão que cria as tabelas no banco de dados
def criar_tabelas():
    db = get_db()
    db.execute('DROP TABLE IF EXISTS usuarios')  #Remove a tabela antiga 
    db.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL
                )''')
    db.execute('''CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    categoria TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data TEXT NOT NULL,
                    descricao TEXT,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
                )''')
    db.commit()

# rotas do flask 
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/registrar', methods=['GET', 'POST']) #define a rota do /refistrar que aceitas o GET e POST
def registrar():
    if request.method == 'POST': #verifica se o metodo de req. é post
        nome = request.form['nome'].strip() #obtem formulario e remove espaços em branco
        senha = request.form['senha']
        if not nome or not senha: #verifica se existe campo vazio em senha ou nome
            return render_template('registrar.html', erro='Preencha todos os campos') #retorna erro na pag de registro
        hashed_password = generate_password_hash(senha) #gera o hash
        db = get_db() #faz a conexão cm o bd
        try:
            db.execute('INSERT INTO usuarios (nome, senha) VALUES (?, ?)', (nome, hashed_password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('registrar.html', erro='Nome de usuário já registrado')
    return render_template('registrar.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        senha = request.form['senha']
        if not nome or not senha:
            return render_template('login.html', erro='Preencha todos os campos')
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE nome = ?', (nome,)).fetchone()
        if usuario and check_password_hash(usuario['senha'], senha):
            session['usuario_id'] = usuario['id']
            session['username'] = usuario['nome']
            return redirect(url_for('dashboard'))
        return render_template('login.html', erro='Credenciais inválidas')
    return render_template('login.html')

@app.route('/logout') #desloga o user
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    filtro = request.args.get('filtro', 'mes')
    db = get_db()
    hoje = datetime.now().date()

    if filtro == 'dia':
        data_inicio = data_fim = hoje
    elif filtro == 'semana':
        data_inicio = hoje - timedelta(days=hoje.weekday())
        data_fim = data_inicio + timedelta(days=6)
    elif filtro == 'ano':
        data_inicio = hoje.replace(month=1, day=1)
        data_fim = hoje.replace(month=12, day=31)
    else:  # mês
        data_inicio = hoje.replace(day=1)
        proximo_mes = data_inicio.replace(day=28) + timedelta(days=4)
        data_fim = proximo_mes - timedelta(days=proximo_mes.day)

    gastos = db.execute('''SELECT * FROM gastos WHERE usuario_id = ? AND data BETWEEN ? AND ? ORDER BY data DESC''',
                        (session['usuario_id'], data_inicio.isoformat(), data_fim.isoformat())).fetchall()
    total = sum(gasto['valor'] for gasto in gastos)
    entradas = 0  # No seu modelo atual, só saídas
    saidas = total

    return render_template('dashboard.html', gastos=gastos, total=total, filtro=filtro, entradas=entradas, saidas=saidas)

@app.route('/add_expense')
def add_expense():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('add_expense.html')

@app.route('/adicionar', methods=['POST'])
def adicionar():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    categoria = request.form.get('categoria', '').strip()
    descricao = request.form.get('descricao', '').strip()
    data = request.form.get('data', '').strip()
    valor_str = request.form.get('valor', '').strip()

    if not categoria or not descricao or not data or not valor_str:
        return render_template('add_expense.html', erro='Todos os campos são obrigatórios')

    try:
        valor = float(valor_str)
        if valor <= 0:
            return render_template('add_expense.html', erro='O valor deve ser positivo')
    except ValueError:
        return render_template('add_expense.html', erro='Valor inválido')

    db = get_db()
    try:
        db.execute('INSERT INTO gastos (usuario_id, categoria, valor, data, descricao) VALUES (?, ?, ?, ?, ?)',
                   (session['usuario_id'], categoria, valor, data, descricao))
        db.commit()
    except Exception as e:
        return render_template('add_expense.html', erro='Erro ao salvar gasto')

    return redirect(url_for('dashboard'))

@app.route('/remover/<int:gasto_id>')
def remover(gasto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    db.execute('DELETE FROM gastos WHERE id = ? AND usuario_id = ?', (gasto_id, session['usuario_id']))
    db.commit()
    return redirect(url_for('dashboard'))

#executa tudo
if __name__ == '__main__':
    with app.app_context():
        criar_tabelas()
    app.run(debug=True)

