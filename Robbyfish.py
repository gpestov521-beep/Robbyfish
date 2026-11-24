import asyncio
import json
import logging
import os
import random
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("BOT_TOKEN", "9262073471:AAHRU9vp2GyBCzpNt-HzXmvfUFjY3uZCt1M")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7883200275"))

bot = Bot(token=TOKEN)
dp = Dispatcher()
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fishing.db")

def get_game_time() -> dict:
    mins = int((time.time() % 3600) * 24 / 60)
    h, m = (mins // 60) % 24, mins % 60
    if 4 <= h < 9: p, n = "morning", "🌅 Утро"
    elif 9 <= h < 18: p, n = "day", "☀️ День"
    elif 18 <= h < 22: p, n = "evening", "🌇 Вечер"
    else: p, n = "night", "🌙 Ночь"
    return {"time_str": f"{h:02d}:{m:02d}", "period": p, "name": n}

def get_weather() -> dict:
    rng = random.Random(int(time.time() // 900))
    return rng.choice([
        {"name": "☀️ Ясно", "bite_mod": 1.0, "pressure": 755},
        {"name": "⛅ Облачно", "bite_mod": 1.25, "pressure": 750},
        {"name": "🌧 Дождь", "bite_mod": 1.4, "pressure": 744},
        {"name": "💨 Ветер", "bite_mod": 0.85, "pressure": 740},
        {"name": "🌫 Туман", "bite_mod": 1.35, "pressure": 752},
    ])

RODS = {
    "bamboo": {"name": "Бамбуковая удочка", "max_weight": 3.0, "price": 0},
    "feeder_light": {"name": "Фидер Волжанка 3.6м", "max_weight": 8.0, "price": 500},
    "spin_pro": {"name": "Спиннинг Shimano", "max_weight": 15.0, "price": 1800},
    "carp_heavy": {"name": "Карповик Fox X5", "max_weight": 35.0, "price": 4500},
    "sea_titan": {"name": "Морской Penn Titan", "max_weight": 140.0, "price": 15000},
}

REELS = {
    "old_reel": {"name": "Невская инерционная", "drag": 2.5, "speed": 1.0, "price": 0},
    "shimano_2500": {"name": "Shimano Catana 2500", "drag": 6.0, "speed": 1.5, "price": 400},
    "daiwa_4000": {"name": "Daiwa Ninja 4000", "drag": 13.0, "speed": 2.0, "price": 1500},
    "penn_8000": {"name": "Penn Slammer 8500", "drag": 32.0, "speed": 2.5, "price": 5000},
    "electric_pro": {"name": "Мульт Shimano 9000", "drag": 110.0, "speed": 3.5, "price": 14000},
}

LINES = {
    "mono_015": {"name": "Моно 0.15мм (2.5кг)", "break_load": 2.5, "visibility": 0.1, "price": 0},
    "mono_025": {"name": "Моно 0.25мм (6.5кг)", "break_load": 6.5, "visibility": 0.3, "price": 200},
    "braid_020": {"name": "Шнур 0.20мм (15кг)", "break_load": 15.0, "visibility": 0.5, "price": 800},
    "braid_035": {"name": "Шнур PE8 (35кг)", "break_load": 35.0, "visibility": 0.7, "price": 2500},
    "kevlar_100": {"name": "Кевлар (135кг)", "break_load": 135.0, "visibility": 0.9, "price": 8000},
}

BAITS = {
    "bread": {"name": "Хлеб", "price": 10}, "worm": {"name": "Червь", "price": 25},
    "boilie": {"name": "Бойлы", "price": 80}, "spoon": {"name": "Колебалка", "price": 150},
    "live_bait": {"name": "Живец", "price": 120}, "squid": {"name": "Кальмар", "price": 300},
}
FISH_SPECIES = {
    "ruff": {"name": "Ерш", "min_w": 0.02, "zachet_w": 0.08, "trophy_w": 0.22, "rare_w": 0.30, "max_w": 0.35, "power": 0.8, "price_kg": 45, "rarity": 85, "best_time": ["night", "morning"], "baits": ["worm"]},
    "bleak": {"name": "Уклейка", "min_w": 0.015, "zachet_w": 0.05, "trophy_w": 0.13, "rare_w": 0.18, "max_w": 0.21, "power": 0.7, "price_kg": 60, "rarity": 95, "best_time": ["day", "morning"], "baits": ["bread"]},
    "gudgeon": {"name": "Пескарь", "min_w": 0.02, "zachet_w": 0.06, "trophy_w": 0.15, "rare_w": 0.20, "max_w": 0.23, "power": 0.8, "price_kg": 55, "rarity": 80, "best_time": ["day"], "baits": ["worm", "bread"]},
    "roach": {"name": "Плотва", "min_w": 0.06, "zachet_w": 0.35, "trophy_w": 1.2, "rare_w": 1.7, "max_w": 2.0, "power": 1.0, "price_kg": 40, "rarity": 90, "best_time": ["morning", "evening"], "baits": ["bread", "worm"]},
    "crucian": {"name": "Карась серебряный", "min_w": 0.08, "zachet_w": 0.5, "trophy_w": 1.9, "rare_w": 2.7, "max_w": 3.2, "power": 1.1, "price_kg": 45, "rarity": 90, "best_time": ["morning", "evening"], "baits": ["bread", "worm", "boilie"]},
    "gold_crucian": {"name": "Карась золотой", "min_w": 0.08, "zachet_w": 0.6, "trophy_w": 2.1, "rare_w": 3.0, "max_w": 3.5, "power": 1.2, "price_kg": 65, "rarity": 55, "best_time": ["morning"], "baits": ["bread", "worm", "boilie"]},
    "bream": {"name": "Лещ", "min_w": 0.3, "zachet_w": 1.5, "trophy_w": 4.4, "rare_w": 6.2, "max_w": 7.0, "power": 1.2, "price_kg": 75, "rarity": 65, "best_time": ["night", "morning"], "baits": ["worm", "boilie"]},
    "white_bream": {"name": "Густера", "min_w": 0.1, "zachet_w": 0.4, "trophy_w": 1.3, "rare_w": 1.8, "max_w": 2.1, "power": 1.0, "price_kg": 55, "rarity": 75, "best_time": ["night", "evening"], "baits": ["worm", "bread"]},
    "ide": {"name": "Язь", "min_w": 0.3, "zachet_w": 1.4, "trophy_w": 4.2, "rare_w": 5.8, "max_w": 6.5, "power": 1.5, "price_kg": 90, "rarity": 50, "best_time": ["morning", "evening"], "baits": ["bread", "worm", "spoon"]},
    "chub": {"name": "Голавль", "min_w": 0.25, "zachet_w": 1.2, "trophy_w": 4.0, "rare_w": 5.5, "max_w": 6.2, "power": 1.7, "price_kg": 95, "rarity": 45, "best_time": ["day"], "baits": ["spoon", "bread"]},
    "tench": {"name": "Линь", "min_w": 0.25, "zachet_w": 1.2, "trophy_w": 3.8, "rare_w": 5.0, "max_w": 5.8, "power": 1.6, "price_kg": 115, "rarity": 35, "best_time": ["morning", "evening"], "baits": ["worm", "boilie"]},
    "perch": {"name": "Окунь", "min_w": 0.08, "zachet_w": 0.4, "trophy_w": 1.6, "rare_w": 2.3, "max_w": 2.7, "power": 1.3, "price_kg": 60, "rarity": 80, "best_time": ["morning", "day"], "baits": ["worm", "spoon"]},
    "pike": {"name": "Щука", "min_w": 0.5, "zachet_w": 2.5, "trophy_w": 12.0, "rare_w": 18.0, "max_w": 22.0, "power": 1.9, "price_kg": 115, "rarity": 50, "best_time": ["morning", "evening"], "baits": ["spoon", "live_bait"]},
    "zander": {"name": "Судак", "min_w": 0.5, "zachet_w": 2.2, "trophy_w": 9.0, "rare_w": 13.5, "max_w": 16.0, "power": 1.8, "price_kg": 140, "rarity": 40, "best_time": ["night", "evening"], "baits": ["live_bait", "spoon"]},
    "asp": {"name": "Жерех", "min_w": 0.6, "zachet_w": 2.0, "trophy_w": 7.5, "rare_w": 10.5, "max_w": 12.5, "power": 2.1, "price_kg": 130, "rarity": 35, "best_time": ["day", "morning"], "baits": ["spoon"]},
    "burbot": {"name": "Налим", "min_w": 0.5, "zachet_w": 2.0, "trophy_w": 9.0, "rare_w": 14.0, "max_w": 17.0, "power": 1.6, "price_kg": 135, "rarity": 40, "best_time": ["night"], "baits": ["live_bait", "worm", "squid"]},
    "eel": {"name": "Угорь", "min_w": 0.4, "zachet_w": 1.2, "trophy_w": 4.0, "rare_w": 6.0, "max_w": 7.2, "power": 2.0, "price_kg": 260, "rarity": 15, "best_time": ["night"], "baits": ["worm", "live_bait"]},
    "common_carp": {"name": "Карп чешуйчатый", "min_w": 1.2, "zachet_w": 4.0, "trophy_w": 20.0, "rare_w": 32.0, "max_w": 38.0, "power": 2.1, "price_kg": 125, "rarity": 45, "best_time": ["morning", "evening"], "baits": ["boilie", "bread"]},
    "mirror_carp": {"name": "Карп зеркальный", "min_w": 1.5, "zachet_w": 4.5, "trophy_w": 23.0, "rare_w": 35.0, "max_w": 42.0, "power": 2.1, "price_kg": 135, "rarity": 35, "best_time": ["morning", "night"], "baits": ["boilie"]},
    "grass_carp": {"name": "Белый амур", "min_w": 1.8, "zachet_w": 5.0, "trophy_w": 26.0, "rare_w": 38.0, "max_w": 45.0, "power": 2.4, "price_kg": 145, "rarity": 30, "best_time": ["day", "morning"], "baits": ["boilie"]},
    "black_carp": {"name": "Черный амур", "min_w": 2.5, "zachet_w": 7.0, "trophy_w": 30.0, "rare_w": 42.0, "max_w": 50.0, "power": 2.6, "price_kg": 190, "rarity": 12, "best_time": ["night"], "baits": ["boilie", "squid"]},
    "sterlet": {"name": "Стерлядь", "min_w": 0.6, "zachet_w": 1.8, "trophy_w": 7.0, "rare_w": 11.0, "max_w": 13.5, "power": 1.8, "price_kg": 340, "rarity": 14, "best_time": ["night", "morning"], "baits": ["worm"]},
    "nelma": {"name": "Нельма", "min_w": 1.2, "zachet_w": 3.5, "trophy_w": 14.0, "rare_w": 21.0, "max_w": 25.0, "power": 2.3, "price_kg": 310, "rarity": 16, "best_time": ["morning", "evening"], "baits": ["spoon", "live_bait"]},
    "taimen": {"name": "Таймень", "min_w": 2.5, "zachet_w": 8.0, "trophy_w": 35.0, "rare_w": 55.0, "max_w": 68.0, "power": 2.8, "price_kg": 300, "rarity": 10, "best_time": ["morning", "evening"], "baits": ["spoon", "live_bait"]},
    "catfish": {"name": "Сом", "min_w": 3.0, "zachet_w": 10.0, "trophy_w": 55.0, "rare_w": 85.0, "max_w": 105.0, "power": 2.5, "price_kg": 170, "rarity": 20, "best_time": ["night"], "baits": ["live_bait", "squid", "worm"]},
    "cod": {"name": "Треска", "min_w": 1.5, "zachet_w": 4.5, "trophy_w": 22.0, "rare_w": 34.0, "max_w": 42.0, "power": 2.0, "price_kg": 195, "rarity": 55, "best_time": ["day", "morning"], "baits": ["squid", "live_bait"]},
    "wolffish": {"name": "Зубатка", "min_w": 2.0, "zachet_w": 5.5, "trophy_w": 18.0, "rare_w": 27.0, "max_w": 32.0, "power": 2.5, "price_kg": 250, "rarity": 25, "best_time": ["day"], "baits": ["squid"]},
    "halibut": {"name": "Палтус", "min_w": 8.0, "zachet_w": 20.0, "trophy_w": 75.0, "rare_w": 110.0, "max_w": 135.0, "power": 3.0, "price_kg": 350, "rarity": 12, "best_time": ["morning", "night"], "baits": ["squid", "live_bait"]},
}

LOCATIONS = {
    "village_pond": {"name": "🏡 Деревенский пруд", "req_lvl": 1, "depth": 2.5, "bottom": "Ил", "desc": "Тихий пруд для старта.", "fish": ["ruff", "bleak", "gudgeon", "roach", "crucian", "gold_crucian", "perch", "tench"]},
    "birch_river": {"name": "🌿 Река Иртыш", "req_lvl": 3, "depth": 6.0, "bottom": "Песок", "desc": "Умеренное течение и хищник.", "fish": ["ruff", "gudgeon", "roach", "white_bream", "bream", "ide", "chub", "perch", "pike", "zander", "asp", "burbot", "eel"]},
    "carp_lake": {"name": "👑 Карподром", "req_lvl": 6, "depth": 4.5, "bottom": "Глина", "desc": "Трофейные карповые.", "fish": ["crucian", "gold_crucian", "tench", "common_carp", "mirror_carp", "grass_carp", "black_carp", "bream"]},
    "taiga_river": {"name": "🌲 Река Туй", "req_lvl": 10, "depth": 9.0, "bottom": "Камни", "desc": "Таймени и гигантские сомы.", "fish": ["ruff", "ide", "chub", "pike", "burbot", "sterlet", "nelma", "taimen", "catfish"]},
    "barents_sea": {"name": "🌊 Баренцево море", "req_lvl": 15, "depth": 45.0, "bottom": "Скалы", "desc": "Морские гиганты!", "fish": ["cod", "wolffish", "halibut"]},
}

def init_db():
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("CREATE TABLE IF NOT EXISTS players (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL)")

@dataclass
class ActiveFight:
    fish_id: str; fish_name: str; weight: float; grade: str; distance: float; tension: float; stamina: float; drag_setting: int; msg_id: int

@dataclass
class Player:
    user_id: int; name: str; money: int = 300; xp: int = 0; level: int = 1; location: str = "village_pond"
    rod: str = "bamboo"; reel: str = "old_reel"; line: str = "mono_015"; bait: str = "bread"
    owned_rods: List[str] = field(default_factory=lambda: ["bamboo"])
    owned_reels: List[str] = field(default_factory=lambda: ["old_reel"])
    owned_lines: List[str] = field(default_factory=lambda: ["mono_015"])
    baits_inv: Dict[str, int] = field(default_factory=lambda: {"bread": 20, "worm": 5})
    keepnet: List[dict] = field(default_factory=list)
    fight: Optional[ActiveFight] = None

USERS_DB: Dict[int, Player] = {}
def save_player(p: Player):
    d = {k: getattr(p, k) for k in ("user_id", "name", "money", "xp", "level", "location", "rod", "reel", "line", "bait", "owned_rods", "owned_reels", "owned_lines", "baits_inv", "keepnet")}
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        conn.execute("INSERT OR REPLACE INTO players (user_id, data) VALUES (?, ?)", (p.user_id, json.dumps(d, ensure_ascii=False)))

def get_player(user: types.User) -> Player:
    if user.id in USERS_DB: return USERS_DB[user.id]
    with sqlite3.connect(DB_PATH, timeout=15) as conn:
        row = conn.execute("SELECT data FROM players WHERE user_id = ?", (user.id,)).fetchone()
    p = Player(**json.loads(row)) if row else Player(user_id=user.id, name=user.first_name)
    if not row: save_player(p)
    USERS_DB[user.id] = p
    return p

def add_xp(p: Player, amount: int) -> str:
    p.xp += amount; msg = ""
    while p.xp >= p.level * 250:
        p.xp -= p.level * 250; p.level += 1
        msg = f"\n🎉 <b>НОВЫЙ УРОВЕНЬ: {p.level}!</b>"
    save_player(p)
    return msg

def generate_bite(p: Player) -> Optional[dict]:
    loc, weather, gtime, vis = LOCATIONS[p.location], get_weather(), get_game_time(), LINES[p.line]["visibility"]
    pool, weights = [], []
    for fid in loc["fish"]:
        f = FISH_SPECIES[fid]
        if p.bait in f["baits"]:
            w = f["rarity"] * (1.8 if gtime["period"] in f["best_time"] else 1.0)
            if f["rarity"] <= 50: w *= max(0.25, 1.2 - vis)
            pool.append((fid, f)); weights.append(w)
    if not pool or random.random() > 0.68 * weather["bite_mod"]: return None
    fid, f = random.choices(pool, weights=weights, k=1)
    boost = 1.35 if p.bait in ("boilie", "live_bait", "squid") else 1.0
    r = random.random()
    if r < 0.0025 * boost: g, w = "rare", round(random.uniform(f["rare_w"], f["max_w"]), 3)
    elif r < 0.018 * boost: g, w = "trophy", round(random.uniform(f["trophy_w"], f["rare_w"] - 0.001), 3)
    elif r < 0.58: g, w = "zachet", round(f["zachet_w"] + (f["trophy_w"] - f["zachet_w"]) * (random.random() ** 1.8), 3)
    else: g, w = "unranked", round(random.uniform(f["min_w"], f["zachet_w"] - 0.001), 3)
    return {"fish_id": fid, "name": f["name"], "weight": w, "grade": g}

def render_fight_text(p: Player) -> str:
    f = p.fight; b = int(f.tension // 10)
    t_bar = ("🟩" * min(b, 5) + "🟨" * max(0, min(b - 5, 3)) + "🟥" * max(0, b - 8)).ljust(10, "⬜")
    s_bar = ("🟦" * int(f.stamina // 10)).ljust(10, "⬜")
    tag = {"trophy": "🟡 ТРОФЕЙ! ", "rare": "🔵 СИНИЙ ТРОФЕЙ! "}.get(f.grade, "")
    return f"🎣 <b>ВЫВАЖИВАНИЕ!</b> {tag}\n🐟 <b>{f.fish_name}</b> (~{f.weight:.1f}кг)\n📏 Дистанция: <b>{f.distance:.1f}м</b> | ⚙️ Фрикцион: <b>{f.drag_setting}%</b>\n\n📈 Натяжение ({int(f.tension)}%):\n{t_bar}\n⚡️ Силы ({int(f.stamina)}%):\n{s_bar}"

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎣 ЗАБРОСИТЬ", callback_data="cast")],
        [InlineKeyboardButton(text="🎒 Снасти", callback_data="gear"), InlineKeyboardButton(text="🪣 Садок", callback_data="keepnet")],
        [InlineKeyboardButton(text="🗺 Локации", callback_data="locations"), InlineKeyboardButton(text="🏪 Магазин", callback_data="shop")],
    ])

@dp.message(Command("start"))
async def cmd_start(m: types.Message):
    p = get_player(m.from_user); w, gt, loc = get_weather(), get_game_time(), LOCATIONS[p.location]
    await m.answer(f"👤 Ур. <b>{p.level}</b> ({p.xp}/{p.level*250}) | 💰 <b>{p.money}₽</b>\n📍 <b>{loc['name']}</b> | 🕒 <b>{gt['name']} ({gt['time_str']})</b> | 🌤 {w['name']}\n🛠 {RODS[p.rod]['name']} | {REELS[p.reel]['name']} | {LINES[p.line]['name']}\n🪱 {BAITS[p.bait]['name']} ({p.baits_inv.get(p.bait, 0)} шт.)", reply_markup=main_menu_kb(), parse_mode="HTML")

    @dp.callback_query(F.data == "cast")
async def cb_cast(c: types.CallbackQuery):
    p = get_player(c.from_user)
    if p.fight: return await c.answer("Уже тянете рыбу!", show_alert=True)
    if p.baits_inv.get(p.bait, 0) <= 0: return await c.answer("Нет наживки!", show_alert=True)
    p.baits_inv[p.bait] -= 1; save_player(p)
    await c.message.edit_text(f"🌊 Заброс на <b>{LOCATIONS[p.location]['name']}</b>...\n⏳ <i>Ждем поклевку...</i>", parse_mode="HTML")
    await asyncio.sleep(random.uniform(2.0, 3.5))
    bite = generate_bite(p)
    if not bite:
        return await c.message.edit_text("🍃 <b>Тишина...</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Ещё раз", callback_data="cast"), InlineKeyboardButton(text="🔙 Меню", callback_data="menu")]]), parse_mode="HTML")
    p.fight = ActiveFight(bite["fish_id"], bite["name"], bite["weight"], bite["grade"], round(random.uniform(15.0, 35.0), 1), 35.0, 100.0, 50, c.message.message_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Подтянуть", callback_data="fight_reel"), InlineKeyboardButton(text="🎣 Выкачать", callback_data="fight_pull")], [InlineKeyboardButton(text="➖ Фрикцион", callback_data="drag_down"), InlineKeyboardButton(text="➕ Фрикцион", callback_data="drag_up")]])
    await c.message.edit_text(render_fight_text(p), reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.in_({"fight_reel", "fight_pull", "drag_down", "drag_up"}))
async def cb_fight(c: types.CallbackQuery):
    p = get_player(c.from_user); f = p.fight
    if not f: return await c.answer("Рыба ушла.")
    rod, reel, line, sp = RODS[p.rod], REELS[p.reel], LINES[p.line], FISH_SPECIES[f.fish_id]
    force = f.weight * sp["power"] * (0.4 + 0.6 * (f.stamina / 100))
    limit = min(rod["max_weight"], line["break_load"])
    if c.data == "drag_down": f.drag_setting = max(10, f.drag_setting - 15)
    elif c.data == "drag_up": f.drag_setting = min(100, f.drag_setting + 15)
    elif c.data == "fight_reel":
        f.tension += 18 if f.tension > 80 else (force / limit) * 22
        if f.tension <= 80: f.distance = max(0.0, f.distance - reel["speed"] * (1.2 if f.stamina < 30 else 0.7)); f.stamina = max(0.0, f.stamina - 8)
    elif c.data == "fight_pull":
        f.distance = max(0.0, f.distance - reel["speed"] * 1.3); f.tension += (force / limit) * 32; f.stamina = max(0.0, f.stamina - 16)
    if random.random() < 0.45 and f.stamina > 15:
        surge = (force / limit) * 28
        if force > reel["drag"] * (f.drag_setting / 100.0): f.distance += round(random.uniform(1.5, 4.0), 1); f.tension += surge * 0.4
        else: f.tension += surge
    else: f.tension = max(10.0, f.tension - 10)
    b_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎣 Забросить", callback_data="cast"), InlineKeyboardButton(text="🔙 Меню", callback_data="menu")]])
    if f.tension >= 100:
        p.fight = None; return await c.message.edit_text(f"💥 <b>ОБРЫВ!</b> ({f.fish_name}) ушла.", reply_markup=b_kb, parse_mode="HTML")
    if f.tension <= 12 and c.data == "drag_down":
        p.fight = None; return await c.message.edit_text(f"💨 <b>СХОД!</b> <b>{f.fish_name}</b> сошла.", reply_markup=b_kb, parse_mode="HTML")
    if f.distance <= 0:
        p.fight = None; pm, xm, badge = {"unranked": (0.35, 0.5, "⚪ Незачет"), "zachet": (1.0, 1.0, "🟢 Зачет"), "trophy": (2.5, 3.0, "🟡 ТРОФЕЙ!"), "rare": (6.0, 8.0, "🔵 СИНИЙ ТРОФЕЙ!")}[f.grade]
        pr, xp = max(1, int(f.weight * sp["price_kg"] * pm)), max(5, int(f.weight * 30 * xm) + 10)
        p.keepnet.append({"name": f.fish_name, "weight": f.weight, "price": pr, "grade": f.grade}); lvl = add_xp(p, xp); save_player(p)
        return await c.message.edit_text(f"✅ <b>ПОЙМАНО!</b> [{badge}]\n🐟 <b>{f.fish_name}</b> — <b>{f.weight:.3f}кг</b>\n💰 <b>{pr}₽</b> | ✨ <b>+{xp} XP</b>{lvl}", reply_markup=b_kb, parse_mode="HTML")
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Подтянуть", callback_data="fight_reel"), InlineKeyboardButton(text="🎣 Выкачать", callback_data="fight_pull")], [InlineKeyboardButton(text="➖ Фрикцион", callback_data="drag_down"), InlineKeyboardButton(text="➕ Фрикцион", callback_data="drag_up")]])
    await c.message.edit_text(render_fight_text(p), reply_markup=kb, parse_mode="HTML")

@dp.callback_query(F.data.in_({"locations", "gear", "shop", "keepnet", "sell_all"}) | F.data.startswith(("setloc_", "eq_", "buy_")))
async def cb_menus(c: types.CallbackQuery):
    p = get_player(c.from_user); d = c.data
    if d.startswith("setloc_"): p.location = d[7:]; save_player(p); return await cb_menu(c)
    if d.startswith("eq_"):
        _, cat, iid = d.split("_", 2); setattr(p, cat, iid); save_player(p); d = "gear"
    if d.startswith("buy_"):
        _, cat, iid = d.split("_", 2); pr = {"rod": RODS, "reel": REELS, "line": LINES, "bait": BAITS}[cat][iid]["price"]
        if p.money < pr: return await c.answer("Мало денег!", show_alert=True)
        p.money -= pr
        if cat == "bait": p.baits_inv[iid] = p.baits_inv.get(iid, 0) + 10
        else: getattr(p, f"owned_{cat}s").append(iid); setattr(p, cat, iid)
        save_player(p); await c.answer("Куплено!"); d = "shop"
    if d == "sell_all":
        tot = sum(x["price"] for x in p.keepnet); p.money += tot; p.keepnet.clear(); save_player(p)
        await c.answer(f"+{tot}₽!", show_alert=True); return await cb_menu(c)
    btns, txt = [], ""
    if d == "locations":
        txt = "🗺 <b>ВОДОЕМЫ:</b>\n"
        for lid, l in LOCATIONS.items():
            req = l["req_lvl"]
            st = "✅" if p.level >= req else f"🔒({req}ур)"
            txt += f"\n<b>{l['name']}</b> {st} — {l['desc']}"
            if p.level >= req: btns.append(InlineKeyboardButton(text=l["name"], callback_data=f"setloc_{lid}"))
    elif d == "gear":
        txt = "🎒 <b>СНАРЯЖЕНИЕ:</b>"
        for rid in p.owned_rods: btns.append(InlineKeyboardButton(text=f"{'✅' if p.rod==rid else ''}🎣{RODS[rid]['name']}", callback_data=f"eq_rod_{rid}"))
        for reid in p.owned_reels: btns.append(InlineKeyboardButton(text=f"{'✅' if p.reel==reid else ''}⚙️{REELS[reid]['name']}", callback_data=f"eq_reel_{reid}"))
        for lid in p.owned_lines: btns.append(InlineKeyboardButton(text=f"{'✅' if p.line==lid else ''}🧵{LINES[lid]['name']}", callback_data=f"eq_line_{lid}"))
        for bid, cnt in p.baits_inv.items():
            if cnt > 0: btns.append(InlineKeyboardButton(text=f"{'✅' if p.bait==bid else ''}🪱{BAITS[bid]['name']}({cnt})", callback_data=f"eq_bait_{bid}"))
    elif d == "shop":
        txt = f"🏪 <b>МАГАЗИН</b> | 💰 <b>{p.money}₽</b>"
        for rid, x in RODS.items():
            if rid not in p.owned_rods: btns.append(InlineKeyboardButton(text=f"🎣{x['name']}({x['price']}₽)", callback_data=f"buy_rod_{rid}"))
        for reid, x in REELS.items():
            if reid not in p.owned_reels: btns.append(InlineKeyboardButton(text=f"⚙️{x['name']}({x['price']}₽)", callback_data=f"buy_reel_{reid}"))
        for lid, x in LINES.items():
            if lid not in p.owned_lines: btns.append(InlineKeyboardButton(text=f"🧵{x['name']}({x['price']}₽)", callback_data=f"buy_line_{lid}"))
        for bid, x in BAITS.items(): btns.append(InlineKeyboardButton(text=f"🪱{x['name']}x10({x['price']}₽)", callback_data=f"buy_bait_{bid}"))
    elif d == "keepnet":
        if not p.keepnet: return await c.message.edit_text("🪣 <b>Садок пуст.</b>", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Меню", callback_data="menu")]]), parse_mode="HTML")
        tot_p = sum(x["price"] for x in p.keepnet); icons = {"unranked": "⚪", "zachet": "🟢", "trophy": "🟡", "rare": "🔵"}
        txt = "🪣 <b>САДОК:</b>\n" + "\n".join(f"• {icons.get(x['grade'],'🟢')} {x['name']} {x['weight']:.2f}кг ({x['price']}₽)" for x in p.keepnet[-15:]) + f"\n\n💰 Итого: <b>{tot_p}₽</b>"
        btns.append(InlineKeyboardButton(text=f"💵 Продать (+{tot_p}₽)", callback_data="sell_all"))
    rows = [btns[i:i+2] for i in range(0, len(btns), 2)] + [[InlineKeyboardButton(text="🔙 Menu", callback_data="menu")]]
    await c.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML")

@dp.message(Command("backup"))
async def cmd_backup(m: types.Message):
    if m.from_user.id == ADMIN_ID and os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn: conn.execute("PRAGMA wal_checkpoint(FULL);")
        await m.answer_document(FSInputFile(DB_PATH, filename=f"backup_{int(time.time())}.db"))

@dp.message(Command("restore"))
async def cmd_restore(m: types.Message):
    if m.from_user.id == ADMIN_ID and m.reply_to_message and m.reply_to_message.document and m.reply_to_message.document.file_name.endswith(".db"):
        fi = await bot.get_file(m.reply_to_message.document.file_id)
        await bot.download_file(fi.file_path, DB_PATH); USERS_DB.clear(); await m.answer("✅ Восстановлено!")

async def main():
    init_db(); await bot.delete_webhook(drop_pending_updates=True); await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
