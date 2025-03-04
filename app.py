from flask import Flask, request, jsonify
from flask_cors import CORS  # Enable CORS
from database.operations import (
    get_account, create_account, set_daily_reward_timer,
    rank_xp_lvl_update, update_account_leaves, recalc_user_rank,
    players_leaderboard
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
    # Here, "leaves" is treated as the increment (the reward amount to add)
    increment = data.get('leaves')
    if increment is None:
        return jsonify({'error': 'Не было передано количество валюты'}), 400
    update_account_leaves(username, increment)
    new_rank = recalc_user_rank(username)
    return jsonify({'message': 'Кол-во валюты успешно сохранено', 'rank': new_rank}), 200

@app.route('/account/<username>/set_wheel_timer', methods=['POST'])
def set_timer(username):
    if not username:
        return jsonify({'error': 'username is required'}), 400

    db_answer = set_daily_reward_timer(username)
    if db_answer == 1:
        return jsonify({'error': 'Account not found'}), 404
    elif db_answer == 0:
        return jsonify({'message': 'Timer updated successfully'}), 200
    elif db_answer == 2:
        return jsonify({'error': '24 hours have not passed yet'}), 403
    else:
        return jsonify({'error': str(db_answer)}), 404

@app.route('/account/<username>/update_xp_system', methods=['PUT'])
def update_xp_system(username):
    data = request.get_json()
    xp = data.get('xp')
    lvl = data.get('lvl')

    if not username:
        return jsonify({'error': 'Нет имени'}), 400

    if xp is None or lvl is None:
        return jsonify({'error': 'Нет хп или левела'}), 400

    # Update XP and level (ignoring any rank value sent from the client)
    rank_xp_lvl_update(username, None, xp, lvl)
    new_rank = recalc_user_rank(username)
    return jsonify({'message': 'Данные успешно сохранены', 'rank': new_rank}), 200

@app.route('/account/leaderboard/players', methods=['GET'])
def get_leaderboard_players():
    data = players_leaderboard()
    if data:
        # Optionally, attach rank info to each player based on list order:
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
