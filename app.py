from flask import Flask, request, jsonify
from flask_cors import CORS  # Enable CORS
from database.operations import (
    get_account, create_account, set_daily_reward_timer_operation,
    xp_update, update_account_leaves, recalc_user_rank,
    players_leaderboard, set_wheel_timer_operation, set_avatar_event
)
from database.operations import start_db, start_mysql_server, stop_mysql_server

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/account/<username>', methods=['GET'])
def get_account_info(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400
    account = get_account(username)
    if account:
        return jsonify(account)
    else:
        return jsonify({'error': 'Аккаунт не найден'}), 404

@app.route('/account', methods=['POST'])
def create_new_account():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Нет имени'}), 400
    if create_account(username, 0, 0, 50, 1):
        return jsonify({'message': 'Аккаунт успешно создан'}), 201
    else:
        return jsonify({'error': 'Уже существует'}), 400

@app.route('/account/<username>/leaves', methods=['PUT'])
def update_leaves(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400
    data = request.get_json()
    increment = data.get('leaves')
    if not increment:
        return jsonify({'error': 'Не было передано количество валюты'}), 400
    update_account_leaves(username, increment)
    new_rank = recalc_user_rank(username)
    return jsonify({'message': 'Кол-во валюты успешно сохранено', 'rank': new_rank}), 200

@app.route('/account/<username>/set_daily_reward_timer', methods=['POST'])
def set_daily_reward_timer(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400
    db_answer = set_daily_reward_timer_operation(username)
    if db_answer == 1:
        return jsonify({'error': 'Account not found'}), 404
    elif db_answer == 0:
        return jsonify({'message': 'Timer updated successfully'}), 200
    elif db_answer == 2:
        return jsonify({'error': '24 hours have not passed yet'}), 403
    else:
        return jsonify({'error': str(db_answer)}), 404

@app.route('/account/<username>/set_wheel_timer', methods=['POST'])
def set_wheel_timer(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400
    db_answer = set_wheel_timer_operation(username)
    if db_answer == 1:
        return jsonify({'error': 'Account not found'}), 404
    elif db_answer == 0:
        return jsonify({'message': 'Timer updated successfully'}), 200
    elif db_answer == 2:
        return jsonify({'error': '30 minutes have not passed yet'}), 403
    else:
        return jsonify({'error': str(db_answer)}), 404

@app.route('/account/<username>/avatar_update', methods=['PUT'])
def avatar_update(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400
    data = request.get_json()
    avatar = data.get('avatar')
    if avatar is None:
        return jsonify({'error': 'Не был передан id аватара'}), 400
    set_avatar_event(username, avatar)
    return jsonify({'message': 'Аватар успешно установлен'}), 200

@app.route('/account/<username>/update_xp_system', methods=['PUT'])
def update_xp_system(username):
    data = request.get_json()
    xp = data.get('xp')
    if not username:
        return jsonify({'error': 'Нет имени'}), 400
    if xp is None:
        return jsonify({'error': 'Нет хп или левела'}), 400
    xp_update(username, xp)
    return jsonify({'message': 'Данные успешно сохранены'}), 200

@app.route('/account/leaderboard/players', methods=['GET'])
def get_leaderboard_players():
    data = players_leaderboard()
    if data:
        ranked = []
        for index, player in enumerate(data):
            player['rank'] = index + 1
            ranked.append(player)
        return jsonify(ranked)
    else:
        return jsonify({'error': 'Данных нет'}), 404

if __name__ == '__main__':
    start_mysql_server()
    start_db()
    app.run(debug=True)
    stop_mysql_server()
