from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nicolas-vtt-secret-key-123'
socketio = SocketIO(app, cors_allowed_origins="*")

# Usuários do Sistema
users_db = {
    "fumagalli": {"password": "30/03/2009", "role": "master_admin"}
}

# Banco de dados completo do Nicolas VTT
game_state = {
    "settings": {
        "backgroundUrl": "https://images.unsplash.com/photo-1605806616949-1e87b487cb2a?q=80&w=1920",
        "themeColor": "#4f46e5",
        "audioUrl": "",
        "isPlaying": False
    },
    "templates": {
        "tmpl_padrao": {
            "id": "tmpl_padrao",
            "name": "Sistema D20",
            "fields": [
                {"id": "hp", "name": "Vida", "type": "resource"},
                {"id": "forca", "name": "Força", "type": "number"}
            ]
        }
    },
    "characters": {},
    "boardTokens": {},
    "chatLog": [] # Histórico de Dados
}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_info = users_db.get(session['username'], {"role": "player"})
    return render_template('index.html', username=session['username'], role=user_info['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users_db and users_db[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Acesso Negado.'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@socketio.on('connect')
def handle_connect():
    emit('sync_state', game_state)

@socketio.on('create_user')
def handle_create_user(data):
    if session.get('username') and users_db.get(session['username'], {}).get('role') == 'master_admin':
        users_db[data['username']] = {"password": data['password'], "role": data['role']}
        emit('user_created', {"success": True, "msg": "Usuário criado!"})

# Atualizações Gerais (Mesa, Fichas, Personagens)
@socketio.on('update_state')
def handle_update_state(data):
    category = data['category'] # settings, templates, characters, boardTokens
    item_id = data.get('id')
    value = data['value']
    
    if item_id:
        game_state[category][item_id] = value
    else:
        game_state[category].update(value)
        
    emit('sync_state', game_state, broadcast=True)

# Remoção da mesa
@socketio.on('remove_token')
def handle_remove_token(char_id):
    if char_id in game_state['boardTokens']:
        del game_state['boardTokens'][char_id]
        emit('sync_state', game_state, broadcast=True)

# Rolagem de Dados
@socketio.on('roll_dice')
def handle_roll_dice(data):
    sides = data['sides']
    player = session.get('username', 'Desconhecido')
    result = random.randint(1, sides)
    
    msg = {"id": random.randint(1000,9999), "player": player, "dice": f"D{sides}", "result": result}
    game_state['chatLog'].append(msg)
    # Mantém apenas os últimos 20 rolagens
    if len(game_state['chatLog']) > 20:
        game_state['chatLog'].pop(0)
        
    emit('sync_state', game_state, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
