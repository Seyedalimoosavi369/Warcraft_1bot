from flask import Flask, send_file, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import os, random, time, json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'warcraft_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}
pvp_queue = []
active_battles = {}

HEROES = {
    "death_knight": {"name":"Death Knight","evolved":"Lich King","type":"Strength","hp":620,"atk":52,"def":8,"icon":"💀",
        "skills":[
            {"name":"Death Coil","dmg":80,"mana":30,"cooldown":8,"effect":"drain","desc":"جان دشمن رو میمکه"},
            {"name":"Animate Dead","dmg":0,"mana":50,"cooldown":15,"effect":"heal","desc":"۱۰۰ HP بازیابی میکنه"}
        ]},
    "paladin": {"name":"Paladin","evolved":"Ashbringer","type":"Strength","hp":600,"atk":48,"def":12,"icon":"⚔️",
        "skills":[
            {"name":"Holy Light","dmg":0,"mana":40,"cooldown":10,"effect":"heal","desc":"۱۵۰ HP بازیابی"},
            {"name":"Divine Shield","dmg":0,"mana":60,"cooldown":20,"effect":"shield","desc":"۳ ثانیه مصون"}
        ]},
    "far_seer": {"name":"Far Seer","evolved":"Warchief","type":"Strength","hp":580,"atk":50,"def":10,"icon":"🌩️",
        "skills":[
            {"name":"Chain Lightning","dmg":120,"mana":35,"cooldown":8,"effect":"stun","desc":"صاعقه زنجیری"},
            {"name":"Earthquake","dmg":90,"mana":55,"cooldown":18,"effect":"slow","desc":"دشمن رو کند میکنه"}
        ]},
    "beastmaster": {"name":"Beastmaster","evolved":"Warlord","type":"Strength","hp":650,"atk":55,"def":7,"icon":"🐗",
        "skills":[
            {"name":"Stampede","dmg":100,"mana":40,"cooldown":12,"effect":"stun","desc":"دشمن رو stun میکنه"},
            {"name":"War Drums","dmg":0,"mana":30,"cooldown":15,"effect":"buff","desc":"ATK رو ۲۰ زیاد میکنه"}
        ]},
    "demon_hunter": {"name":"Demon Hunter","evolved":"Betrayer","type":"Agility","hp":520,"atk":65,"def":5,"icon":"😈",
        "skills":[
            {"name":"Mana Burn","dmg":60,"mana":25,"cooldown":6,"effect":"mana_burn","desc":"مانای دشمن میسوزه"},
            {"name":"Metamorphosis","dmg":150,"mana":80,"cooldown":25,"effect":"transform","desc":"تبدیل به دیو"}
        ]},
    "warden": {"name":"Warden","evolved":"Shadowblade","type":"Agility","hp":500,"atk":68,"def":4,"icon":"🗡️",
        "skills":[
            {"name":"Fan of Knives","dmg":110,"mana":35,"cooldown":8,"effect":"bleed","desc":"خونریزی ایجاد میکنه"},
            {"name":"Blink","dmg":0,"mana":20,"cooldown":10,"effect":"dodge","desc":"حمله بعدی رو dodge میکنه"}
        ]},
    "shadow_hunter": {"name":"Shadow Hunter","evolved":"Voodoo Master","type":"Agility","hp":510,"atk":60,"def":6,"icon":"🧿",
        "skills":[
            {"name":"Hex","dmg":0,"mana":45,"cooldown":12,"effect":"stun","desc":"دشمن رو ۲ ثانیه stun میکنه"},
            {"name":"Big Bad Voodoo","dmg":0,"mana":70,"cooldown":20,"effect":"heal","desc":"۲۰۰ HP بازیابی"}
        ]},
    "axe_thrower": {"name":"Axe Thrower","evolved":"Berserker","type":"Agility","hp":530,"atk":63,"def":5,"icon":"🪓",
        "skills":[
            {"name":"Throw Axe","dmg":95,"mana":25,"cooldown":6,"effect":"bleed","desc":"خونریزی"},
            {"name":"Berserker Rage","dmg":130,"mana":50,"cooldown":15,"effect":"crit","desc":"ضربه بحرانی"}
        ]},
    "archmage": {"name":"Archmage","evolved":"Arcane Lord","type":"Intelligence","hp":460,"atk":75,"def":3,"icon":"🧙",
        "skills":[
            {"name":"Blizzard","dmg":140,"mana":60,"cooldown":12,"effect":"slow","desc":"طوفان یخ"},
            {"name":"Mass Teleport","dmg":0,"mana":80,"cooldown":25,"effect":"shield","desc":"سپر جادویی"}
        ]},
    "lich": {"name":"Lich","evolved":"Lich Overlord","type":"Intelligence","hp":450,"atk":78,"def":2,"icon":"👻",
        "skills":[
            {"name":"Frost Nova","dmg":120,"mana":45,"cooldown":10,"effect":"stun","desc":"دشمن رو منجمد میکنه"},
            {"name":"Death and Decay","dmg":160,"mana":90,"cooldown":30,"effect":"dot","desc":"آسیب مداوم"}
        ]},
    "priestess": {"name":"Priestess of Moon","evolved":"Moon Goddess","type":"Intelligence","hp":470,"atk":70,"def":4,"icon":"🌙",
        "skills":[
            {"name":"Starfall","dmg":130,"mana":55,"cooldown":12,"effect":"aoe","desc":"باران ستاره"},
            {"name":"Trueshot Aura","dmg":80,"mana":30,"cooldown":8,"effect":"buff","desc":"ATK رو ۱۵ زیاد میکنه"}
        ]},
    "prophet": {"name":"Prophet","evolved":"Medivh Reborn","type":"Intelligence","hp":455,"atk":72,"def":3,"icon":"🔮",
        "skills":[
            {"name":"Force of Nature","dmg":110,"mana":50,"cooldown":12,"effect":"summon","desc":"درختان جنگجو"},
            {"name":"Silence","dmg":0,"mana":40,"cooldown":15,"effect":"silence","desc":"دشمن نمیتونه اسکیل بزنه"}
        ]},
}

BASE_ITEMS = {
    "sword": {"name":"Sword ⚔️","atk":15,"def":0,"price":200,"icon":"⚔️"},
    "shield": {"name":"Shield 🛡️","atk":0,"def":20,"price":250,"icon":"🛡️"},
    "armor": {"name":"Armor 🥋","atk":0,"def":15,"price":180,"icon":"🥋"},
    "boots": {"name":"Boots 👢","atk":5,"def":5,"price":150,"icon":"👢"},
    "staff": {"name":"Staff 🪄","atk":25,"def":0,"price":300,"icon":"🪄"},
    "cloak": {"name":"Cloak 🔥","atk":10,"def":10,"price":220,"icon":"🔥"},
    "ring": {"name":"Ring 💍","atk":8,"def":8,"price":180,"icon":"💍"},
    "gem": {"name":"Gem 💎","atk":12,"def":12,"price":280,"icon":"💎"},
}

CRAFTED_ITEMS = {
    "holy_sword": {"name":"Holy Sword ✨⚔️","atk":40,"def":10,"recipe":["sword","gem"],"icon":"✨⚔️"},
    "dragon_armor": {"name":"Dragon Armor 🐉","atk":5,"def":50,"recipe":["armor","cloak"],"icon":"🐉"},
    "arcane_staff": {"name":"Arcane Staff 🌟","atk":60,"def":0,"recipe":["staff","gem"],"icon":"🌟"},
    "thunder_boots": {"name":"Thunder Boots ⚡","atk":15,"def":15,"recipe":["boots","ring"],"icon":"⚡"},
    "shadow_cloak": {"name":"Shadow Cloak 🌑","atk":20,"def":30,"recipe":["cloak","shield"],"icon":"🌑"},
    "demon_blade": {"name":"Demon Blade 😈⚔️","atk":70,"def":5,"recipe":["sword","staff"],"icon":"😈⚔️"},
    "holy_armor": {"name":"Holy Armor 🛡️✨","atk":10,"def":60,"recipe":["armor","shield"],"icon":"🛡️✨"},
    "arcane_ring": {"name":"Arcane Ring 💍🌟","atk":25,"def":25,"recipe":["ring","gem"],"icon":"💍🌟"},
}

@app.route('/')
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))

@socketio.on('connect')
def on_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in players:
        if sid in pvp_queue:
            pvp_queue.remove(sid)
        if sid in active_battles:
            battle = active_battles[sid]
            enemy_sid = battle['enemy_sid']
            if enemy_sid in active_battles:
                socketio.emit('enemy_fled', {}, room=enemy_sid)
                del active_battles[enemy_sid]
            del active_battles[sid]
        del players[sid]

@socketio.on('join_game')
def on_join(data):
    sid = request.sid
    hero_id = data.get('hero_id')
    player_data = data.get('player')
    if hero_id and hero_id in HEROES:
        h = HEROES[hero_id]
        players[sid] = {
            'sid': sid,
            'hero_id': hero_id,
            'hero': h,
            'level': player_data.get('level', 1),
            'hp': player_data.get('hp', h['hp']),
            'max_hp': player_data.get('max_hp', h['hp']),
            'atk': player_data.get('atk', h['atk']),
            'def': player_data.get('def', h['def']),
            'mana': player_data.get('mana', 100),
            'max_mana': 100,
            'coins': player_data.get('coins', 500),
            'items': player_data.get('items', []),
            'skill_cd': [0, 0],
            'effects': [],
            'silenced': False,
        }
        emit('game_joined', {'hero': h, 'player': players[sid]})

@socketio.on('join_pvp')
def on_join_pvp():
    sid = request.sid
    if sid not in players:
        return
    if sid in active_battles:
        emit('already_in_battle')
        return
    
    player = players[sid]
    partner_sid = None
    
    for q_sid in pvp_queue:
        if q_sid != sid and q_sid in players:
            q_player = players[q_sid]
            if abs(q_player['level'] - player['level']) <= 3:
                partner_sid = q_sid
                break
    
    if partner_sid:
        pvp_queue.remove(partner_sid)
        room = f"battle_{sid}_{partner_sid}"
        join_room(room)
        socketio.server.enter_room(partner_sid, room, namespace='/')
        
        active_battles[sid] = {'enemy_sid': partner_sid, 'room': room, 'turn': sid}
        active_battles[partner_sid] = {'enemy_sid': sid, 'room': room, 'turn': sid}
        
        p1 = players[sid]
        p2 = players[partner_sid]
        
        socketio.emit('battle_start', {
            'my_hero': p1['hero'],
            'my_hp': p1['hp'],
            'my_max_hp': p1['max_hp'],
            'my_atk': p1['atk'],
            'my_def': p1['def'],
            'my_mana': p1['mana'],
            'my_level': p1['level'],
            'enemy_hero': p2['hero'],
            'enemy_hp': p2['hp'],
            'enemy_max_hp': p2['max_hp'],
            'enemy_level': p2['level'],
            'your_turn': True,
        }, room=sid)
        
        socketio.emit('battle_start', {
            'my_hero': p2['hero'],
            'my_hp': p2['hp'],
            'my_max_hp': p2['max_hp'],
            'my_atk': p2['atk'],
            'my_def': p2['def'],
            'my_mana': p2['mana'],
            'my_level': p2['level'],
            'enemy_hero': p1['hero'],
            'enemy_hp': p1['hp'],
            'enemy_max_hp': p1['max_hp'],
            'enemy_level': p1['level'],
            'your_turn': False,
        }, room=partner_sid)
    else:
        pvp_queue.append(sid)
        emit('waiting_for_player')

@socketio.on('attack')
def on_attack():
    sid = request.sid
    if sid not in active_battles or sid not in players:
        return
    battle = active_battles[sid]
    if battle['turn'] != sid:
        emit('not_your_turn')
        return
    
    player = players[sid]
    enemy_sid = battle['enemy_sid']
    enemy = players[enemy_sid]
    
    dmg = max(1, player['atk'] - enemy['def'] + random.randint(-5, 10))
    enemy['hp'] = max(0, enemy['hp'] - dmg)
    
    battle['turn'] = enemy_sid
    active_battles[enemy_sid]['turn'] = enemy_sid
    
    socketio.emit('attack_result', {
        'dmg': dmg,
        'my_hp': player['hp'],
        'enemy_hp': enemy['hp'],
        'your_turn': False,
        'effect': 'normal',
    }, room=sid)
    
    socketio.emit('attack_result', {
        'dmg': dmg,
        'my_hp': enemy['hp'],
        'enemy_hp': player['hp'],
        'your_turn': True,
        'effect': 'hit',
    }, room=enemy_sid)
    
    if enemy['hp'] <= 0:
        reward = random.randint(100, 300)
        socketio.emit('battle_end', {'result': 'win', 'reward': reward}, room=sid)
        socketio.emit('battle_end', {'result': 'lose', 'reward': 0}, room=enemy_sid)
        del active_battles[sid]
        del active_battles[enemy_sid]

@socketio.on('use_skill')
def on_skill(data):
    sid = request.sid
    if sid not in active_battles or sid not in players:
        return
    battle = active_battles[sid]
    if battle['turn'] != sid:
        emit('not_your_turn')
        return
    
    player = players[sid]
    enemy_sid = battle['enemy_sid']
    enemy = players[enemy_sid]
    skill_idx = data.get('skill_idx', 0)
    
    if player.get('silenced'):
        emit('skill_failed', {'reason': 'silenced'})
        return
    
    now = time.time()
    cd_key = f'skill_cd_{skill_idx}'
    if player.get(cd_key, 0) > now:
        emit('skill_failed', {'reason': 'cooldown', 'remaining': int(player[cd_key] - now)})
        return
    
    hero = HEROES[player['hero_id']]
    if skill_idx >= len(hero['skills']):
        return
    
    skill = hero['skills'][skill_idx]
    if player['level'] < 6 and skill_idx == 1:
        emit('skill_failed', {'reason': 'level_required', 'required': 6})
        return
    
    if player['mana'] < skill['mana']:
        emit('skill_failed', {'reason': 'no_mana'})
        return
    
    player['mana'] -= skill['mana']
    player[cd_key] = now + skill['cooldown']
    
    effect = skill['effect']
    dmg = 0
    heal = 0
    effect_msg = ''
    
    if effect == 'drain':
        dmg = skill['dmg'] + player['level'] * 5
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        player['hp'] = min(player['max_hp'], player['hp'] + dmg // 2)
        effect_msg = f"جان دزدیده شد! +{dmg//2} HP"
    elif effect == 'heal':
        heal = skill['dmg'] if skill['dmg'] == 0 else 0
        heal = 150 + player['level'] * 10
        player['hp'] = min(player['max_hp'], player['hp'] + heal)
        effect_msg = f"+{heal} HP بازیابی"
    elif effect == 'shield':
        player['shield'] = True
        effect_msg = "سپر فعال شد!"
    elif effect == 'stun':
        dmg = skill['dmg'] + player['level'] * 4
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"دشمن stun شد! {dmg} دمیج"
    elif effect == 'slow':
        dmg = skill['dmg'] + player['level'] * 3
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"دشمن کند شد! {dmg} دمیج"
    elif effect == 'mana_burn':
        dmg = skill['dmg'] + player['level'] * 3
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        enemy['mana'] = max(0, enemy['mana'] - 30)
        effect_msg = f"مانای دشمن سوخت! {dmg} دمیج"
    elif effect == 'transform':
        dmg = skill['dmg'] + player['level'] * 8
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"تبدیل! {dmg} دمیج"
    elif effect == 'bleed':
        dmg = skill['dmg'] + player['level'] * 4
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"خونریزی! {dmg} دمیج"
    elif effect == 'dodge':
        player['dodge_next'] = True
        effect_msg = "حمله بعدی dodge میشه!"
    elif effect == 'buff':
        player['atk'] += 20
        effect_msg = "+20 ATK!"
    elif effect == 'crit':
        dmg = int((skill['dmg'] + player['level'] * 5) * 1.5)
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"ضربه بحرانی! {dmg} دمیج"
    elif effect == 'dot':
        dmg = skill['dmg'] + player['level'] * 6
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"آسیب مداوم! {dmg} دمیج"
    elif effect == 'silence':
        enemy['silenced'] = True
        effect_msg = "دشمن ساکت شد!"
    elif effect == 'aoe':
        dmg = skill['dmg'] + player['level'] * 5
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"باران ستاره! {dmg} دمیج"
    elif effect == 'summon':
        dmg = skill['dmg'] + player['level'] * 4
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"درختان جنگجو! {dmg} دمیج"
    else:
        dmg = skill['dmg'] + player['level'] * 3
        enemy['hp'] = max(0, enemy['hp'] - dmg)
        effect_msg = f"{dmg} دمیج"
    
    battle['turn'] = enemy_sid
    active_battles[enemy_sid]['turn'] = enemy_sid
    
    socketio.emit('skill_result', {
        'skill_name': skill['name'],
        'effect': effect,
        'effect_msg': effect_msg,
        'dmg': dmg,
        'heal': heal,
        'my_hp': player['hp'],
        'my_mana': player['mana'],
        'enemy_hp': enemy['hp'],
        'your_turn': False,
        'cooldown': skill['cooldown'],
        'skill_idx': skill_idx,
    }, room=sid)
    
    socketio.emit('enemy_skill', {
        'skill_name': skill['name'],
        'effect': effect,
        'effect_msg': effect_msg,
        'dmg': dmg,
        'my_hp': enemy['hp'],
        'enemy_hp': player['hp'],
        'your_turn': True,
    }, room=enemy_sid)
    
    if enemy['hp'] <= 0:
        reward = random.randint(100, 300)
        socketio.emit('battle_end', {'result': 'win', 'reward': reward}, room=sid)
        socketio.emit('battle_end', {'result': 'lose', 'reward': 0}, room=enemy_sid)
        if sid in active_battles: del active_battles[sid]
        if enemy_sid in active_battles: del active_battles[enemy_sid]

@socketio.on('flee_battle')
def on_flee():
    sid = request.sid
    if sid in active_battles:
        enemy_sid = active_battles[sid]['enemy_sid']
        socketio.emit('enemy_fled', {}, room=enemy_sid)
        if sid in active_battles: del active_battles[sid]
        if enemy_sid in active_battles: del active_battles[enemy_sid]
    if sid in pvp_queue:
        pvp_queue.remove(sid)
    emit('fled')

@socketio.on('cancel_queue')
def on_cancel():
    sid = request.sid
    if sid in pvp_queue:
        pvp_queue.remove(sid)
    emit('queue_cancelled')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)
