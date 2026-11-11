from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexus-vtt-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

game_state = {
    "session": {
        "backgroundUrl": "https://images.unsplash.com/photo-1605806616949-1e87b487cb2a?q=80&w=1920",
        "themeColor": "#4f46e5"
    },
    "characters": {},
    "boardTokens": {}
}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('sync_state', game_state)

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
