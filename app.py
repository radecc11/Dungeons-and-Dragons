from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# Chave secreta obrigatória para usar sessões de login no Flask
app.config['SECRET_KEY'] = 'nexus-vtt-secret-key-123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Banco de dados de usuários (Você como Master Admin já está aqui)
users_db = {
    "fumagalli": {"password": "30/03/2009", "role": "master_admin"}
}

# Banco de dados da mesa
game_state = {
    "session": {
        "backgroundUrl": "https://images.unsplash.com/photo-1605806616949-1e87b487cb2a?q=80&w=1920",
        "themeColor": "#4f46e5"
    },
    "characters": {},
    "boardTokens": {}
}

# --- ROTAS DE LOGIN E PÁGINAS ---

@app.route('/')
def index():
    # Se não estiver logado, manda para a tela de login
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Pega as informações do usuário atual
    user_info = users_db.get(session['username'], {"role": "player"})
    return render_template('index.html', username=session['username'], role=user_info['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verifica se o usuário existe e a senha bate
        if username in users_db and users_db[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Usuário ou senha incorretos. Acesso negado.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


# --- COMUNICAÇÃO EM TEMPO REAL (SOCKET.IO) ---

@socketio.on('connect')
def handle_connect():
    emit('sync_state', game_state)

# Nova função: O Master Admin pede para criar uma conta
@socketio.on('create_user')
def handle_create_user(data):
    creator = session.get('username')
    # Verifica se quem está pedindo realmente é o Master Admin
    if creator and users_db.get(creator, {}).get('role') == 'master_admin':
        new_username = data['username']
        new_password = data['password']
        new_role = data['role']
        
        if new_username not in users_db:
            users_db[new_username] = {"password": new_password, "role": new_role}
            emit('user_created', {"success": True, "msg": f"Conta '{new_username}' criada com sucesso!"})
        else:
            emit('user_created', {"success": False, "msg": "Erro: Este usuário já existe."})
    else:
        emit('user_created', {"success": False, "msg": "Sem permissão."})

@socketio.on('add_character')
def handle_add_character(char_data):
    game_state['characters'][char_data['id']] = char_data
    emit('sync_state', game_state, broadcast=True)

@socketio.on('move_token')
def handle_move_token(data):
    game_state['boardTokens'][data['charId']] = {'x': data['x'], 'y': data['y']}
    emit('token_moved', data, broadcast=True)

@socketio.on('toggle_board')
def handle_toggle_board(data):
    char_id = data['charId']
    if char_id in game_state['boardTokens']:
        del game_state['boardTokens'][char_id]
    else:
        game_state['boardTokens'][char_id] = {'x': 200, 'y': 200}
    emit('sync_state', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
