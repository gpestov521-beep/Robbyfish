import asyncio, json, os, random, time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = os.getenv("BOT_TOKEN", "9262073471:AAEVLEbj3_7DTJ-Sl9jkRO4i357dKFTmLGY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "fishing_db.json")

bot = Bot(token=TOKEN)
dp = Dispatcher()
db = json.load(open(DB, encoding="utf-8")) if os.path.exists(DB) else {}

def save():
    with open(DB, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False)

RODS = {
    1: ("🎋 Бамбук", 0, 1.0), 2: ("🎣 Спиннинг", 150, 1.5),
    3: ("⚡ Карбон", 600, 2.2), 4: ("🛡️ Титан", 1800, 3.2),
    5: ("👑 Легенда", 5000, 4.5), 6: ("🔱 Трезубец", 15000, 6.5),
    7: ("🌌 Звёздная", 40000, 9.0), 8: ("⚡ Посейдон", 100000, 13.0),
    9: ("🔥 Феникс", 250000, 18.0), 10: ("❄️ Ледяная", 600000, 25.0),
    11: ("💎 Алмазная", 1400000, 34.0), 12: ("🔮 Мистическая", 3200000, 46.0),
    13: ("🐉 Драконья", 7500000, 62.0), 14: ("☀️ Солнечная", 16000000, 82.0),
    15: ("🌙 Лунная", 35000000, 110.0), 16: ("🌀 Пустота", 75000000, 145.0),
    17: ("⏳ Хронос", 150000000, 190.0), 18: ("⚛️ Квантовая", 320000000, 250.0),
    19: ("👑 Олимп", 700000000, 330.0), 20: ("♾️ Абсолют", 1500000000, 450.0)
}

LOCS = {
    "pond": ("🏞 Пруд", 1, (("👢 Сапог", 1, 2, 20), ("🐟 Карась", 12, 5, 45), ("🐠 Окунь", 18, 8, 25), ("🐸 Лягушка", 25, 12, 10))),
    "river": ("🌊 Река", 2, (("🐟 Плотва", 25, 10, 40), ("🦈 Щука", 65, 20, 35), ("🐊 Судак", 80, 25, 20), ("🐳 Сом", 160, 45, 5))),
    "lake": ("🏔 Озеро", 3, (("🐟 Форель", 90, 30, 40), ("🐠 Хариус", 130, 40, 30), ("🐡 Налим", 180, 55, 20), ("👑 Осетр", 400, 100, 10))),
    "ocean": ("🚢 Океан", 4, (("🐡 Фугу", 150, 45, 35), ("🍣 Тунец", 300, 75, 35), ("🦈 Акула", 750, 140, 20), ("👑 Марлин", 1600, 250, 10))),
    "abyss": ("🌋 Бездна", 5, (("🦑 Кальмар", 500, 120, 40), ("🐉 Удильщик", 1200, 220, 30), ("🦖 Мегалодон", 3000, 450, 20), ("🐙 Кракен", 7000, 900, 10))),
    "space": ("🌌 Космос", 6, (("☄️ Астероид", 2500, 500, 40), ("🛸 НЛО", 6000, 1100, 30), ("👾 Левиафан", 14000, 2200, 20), ("🌟 Звёздный кит", 30000, 4500, 10))),
    "swamp": ("🐊 Болото", 7, (("🐍 Уж", 4500, 800, 40), ("🐢 Черепаха", 9500, 1500, 30), ("🐊 Аллигатор", 20000, 3000, 20), ("🌿 Дух топи", 45000, 6000, 10))),
    "glacier": ("❄️ Ледник", 8, (("🐟 Корюшка", 8000, 1200, 40), ("🦭 Тюлень", 17000, 2400, 30), ("🐋 Нарвал", 36000, 4800, 20), ("🦣 Мамонт", 80000, 9500, 10))),
    "volcano": ("🔥 Вулкан", 9, (("🦎 Саламандра", 15000, 2000, 40), ("🦀 Лавовый краб", 32000, 4000, 30), ("🐍 Огненный змей", 68000, 8000, 20), ("🦅 Феникс", 150000, 16000, 10))),
    "jungle": ("🌴 Джунгли", 10, (("🐟 Пиранья", 28000, 3500, 40), ("⚡ Электрический угорь", 60000, 7000, 30), ("🐍 Анаконда", 130000, 14000, 20), ("🗿 Идол", 280000, 28000, 10))),
    "atlantis": ("🏛 Атлантида", 11, (("🏺 Амфора", 55000, 6000, 40), ("🧜 Тритон", 120000, 12000, 30), ("🤖 Голем", 250000, 24000, 20), ("👑 Посейдон", 550000, 48000, 10))),
    "cyber": ("🤖 Киберсити", 12, (("💾 Чип-рыба", 110000, 10000, 40), ("🦾 Меха-акула", 240000, 20000, 30), ("🛸 Дрон", 500000, 40000, 20), ("🧠 ИИ-Кракен", 1100000, 80000, 10))),
    "underworld": ("💀 Подземелье", 13, (("🦴 Рыба-скелет", 220000, 18000, 40), ("🦇 Гаргулья", 480000, 36000, 30), ("🐺 Цербер", 1000000, 72000, 20), ("😈 Аид", 2200000, 140000, 10))),
    "clouds": ("☁️ Небеса", 14, (("🕊️ Облачный скат", 450000, 30000, 40), ("🦄 Пегас", 950000, 60000, 30), ("🐉 Небесный дракон", 2000000, 120000, 20), ("☀️ Феникс Ра", 4500000, 240000, 10))),
    "blackhole": ("🌀 Чёрная дыра", 15, (("⚛️ Квант", 900000, 50000, 40), ("🕳️ Сингулярность", 1900000, 100000, 30), ("⏳ Пожиратель времени", 4000000, 200000, 20), ("🌌 Творец", 9000000, 400000, 10))),
    "eden": ("✨ Эдем", 16, (("🍎 Золотой карп", 1800000, 85000, 40), ("🦢 Лебедь света", 3800000, 170000, 30), ("🦄 Единорог", 8000000, 340000, 20), ("🌟 Абсолют", 18000000, 700000, 10)))
}

QUESTS = {
    "catch_10": ("Поймать 10 рыб", 10, 200, 80), "catch_25": ("Поймать 25 рыб", 25, 550, 200),
    "catch_50": ("Поймать 50 рыб", 50, 1400, 500), "weight_50": ("Наловить 50 кг", 50, 400, 150),
    "weight_150": ("Наловить 150 кг", 150, 1200, 450), "sell_500": ("Продать на 500 💰", 500, 350, 120)
}

ALL_F = [n for _, _, p in LOCS.values() for n, _, _, _ in p]

def new_q():
    return {"id": random.choice(list(QUESTS)), "prog": 0, "done": False}

def udata(uid, name="Рыбак"):
    u = db.setdefault(str(uid), {
        "name": name, "coins": 0, "rod": 1, "loc": "pond", "bag": [],
        "worms": 0, "lures": 0, "cd": 0, "day": 0, "max": 0.0,
        "lvl": 1, "xp": 0, "quest": new_q(), "dex": {}, "dd": False
    })
    u["name"] = str(name).replace("<", "").replace(">", "")
    u.setdefault("lvl", 1); u.setdefault("xp", 0); u.setdefault("dex", {}); u.setdefault("dd", False)
    if not isinstance(u.get("quest"), dict): u["quest"] = new_q()
    return u

def xp_bar(u):
    need, cur = u["lvl"] * 100, u["xp"]
    left, filled = max(0, need - cur), min(10, int((cur / need) * 10))
    return f"[{'🟩' * filled}{'⬜' * (10 - filled)}] {cur}/{need} XP (до {u['lvl']+1} ур.: {left} XP)"

def add_xp(u, amt):
    u["xp"] += amt
    msg, leveled = "", False
    while u["xp"] >= u["lvl"] * 100:
        u["xp"] -= u["lvl"] * 100
        u["lvl"] += 1
        leveled = True
        msg += f"\n🎊 <b>НОВЫЙ УРОВЕНЬ {u['lvl']}!</b>"
    return msg if leveled else msg + f"\n📊 {xp_bar(u)}"

def upd_q(u, qt, val):
    q = u["quest"]
    if q.get("done") or not q.get("id", "").startswith(qt): return ""
    _, g, rc, rxp = QUESTS.get(q["id"], ("", 10, 100, 50))
    q["prog"] = round(q["prog"] + val, 2)
    if q["prog"] >= g:
        q["prog"], q["done"], u["coins"] = g, True, u["coins"] + rc
        return f"\n✅ <b>КВЕСТ ВЫПОЛНЕН!</b> +{rc} 💰, +{rxp} XP" + add_xp(u, rxp)
    return ""

def kb():
    b = ReplyKeyboardBuilder()
    for t in ("🎣 Закинуть", "🎒 Садок", "🗺 Локации", "🏪 Магазин", "📜 Квесты", "📖 Индекс", "🎁 Бонус", "🏆 Топ"):
        b.button(text=t)
    return b.adjust(2).as_markup(resize_keyboard=True)
@dp.message(CommandStart())
async def start(m: types.Message):
    udata(m.from_user.id, m.from_user.first_name); save()
    await m.answer("Привет, рыбак! 🌊 Закидывай удочку и собирай улов!", reply_markup=kb())

@dp.message(F.text == "🎣 Закинуть")
async def fish(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    if time.time() - u["cd"] < 4:
        return await m.answer(f"⏳ Ждите {round(4 - (time.time() - u['cd']), 1)}с.")
    u["cd"] = time.time()
    ln, _, pool = LOCS.get(u["loc"], LOCS["pond"])
    _, _, ml = RODS.get(u["rod"], RODS[1])
    bm, bt = (1.5, "✨") if u["lures"] > 0 else ((1.2, "🪱") if u["worms"] > 0 else (1.0, "🪝"))
    if u["lures"] > 0: u["lures"] -= 1
    elif u["worms"] > 0: u["worms"] -= 1

    ch_txt = ""
    if random.randint(1, 10) == 1:
        c = random.randint(50, 300) * u["lvl"]
        u["coins"] += c
        ch_txt = f"\n💎 <b>Сундук: +{c} 💰!</b>"

    r, cur, fn, bp, bxp = random.uniform(0, sum(c for _, _, _, c in pool)), 0, "🐟 Карась", 10, 5
    for n, p, xp, c in pool:
        if cur + c >= r:
            fn, bp, bxp = n, p, xp
            break
        cur += c

    w, pr, xpg = round(random.uniform(0.5, 5.0) * ml * bm, 2), int(bp * ml * bm), int(bxp * bm)
    u["bag"].append((fn, w, pr))

    rec_txt = ""
    if w > u["max"]:
        u["max"] = w
        bonus = int(w * 15)
        u["coins"] += bonus
        rec_txt = f"\n🏆 <b>НОВЫЙ РЕКОРД ВЕСА!</b> +{bonus} 💰"

    nd = f"\n🆕 <b>Индекс: {len(u['dex'])+1}/{len(ALL_F)}!</b>" if fn not in u["dex"] else ""
    u["dex"][fn] = max(u["dex"].get(fn, 0), w)
    ext = add_xp(u, xpg) + upd_q(u, "catch", 1) + upd_q(u, "weight", w)
    save()
    await m.answer(f"📍 {ln} {bt}{ch_txt}{rec_txt}\n🎉 <b>{fn}</b> | ⚖️ {w}кг | 💵 {pr}💰 | ⭐ +{xpg}XP{nd}{ext}", parse_mode="HTML", reply_markup=kb())

@dp.message(F.text == "🎒 Садок")
async def bag(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    rn, _, _ = RODS.get(u["rod"], RODS[1])
    head = (
        f"👤 <b>{u['name']}</b> | ⭐ Уровень <b>{u['lvl']}</b>\n📊 {xp_bar(u)}\n"
        f"💰 Баланс: <b>{u['coins']}</b> | 🏆 Рекорд: <b>{u['max']} кг</b>\n"
        f"🎣 Снасть: <b>{rn}</b> | 🪱 {u['worms']} | ✨ {u['lures']}\n\n"
    )
    if not u["bag"]: return await m.answer(head + "🎒 В садке пока пусто.", parse_mode="HTML")
    tot_w, tot_p = round(sum(x[1] for x in u["bag"]), 2), sum(x[2] for x in u["bag"])
    items = "\n".join(f"• {x[0]} — {x[1]} кг ({x[2]} 💰)" for x in u["bag"][-15:])
    more = f"\n<i>...и ещё {len(u['bag'])-15} шт.</i>" if len(u["bag"]) > 15 else ""
    ikb = InlineKeyboardBuilder()
    ikb.button(text=f"💵 Продать всё (+{tot_p} 💰)", callback_data="sell_all")
    await m.answer(f"{head}🐟 Улов ({len(u['bag'])} шт. | {tot_w} кг):\n{items}{more}", parse_mode="HTML", reply_markup=ikb.as_markup())

@dp.callback_query(F.data == "sell_all")
async def sell_all(c: types.CallbackQuery):
    u = udata(c.from_user.id, c.from_user.first_name)
    if not u["bag"]: return await c.answer("Садок уже пуст!", show_alert=True)
    tot_p = sum(x[2] for x in u["bag"])
    u["coins"] += tot_p; u["bag"] = []
    q_txt = upd_q(u, "sell", tot_p); save()
    await c.message.edit_text(f"✅ Весь улов продан за <b>{tot_p} 💰</b>!\nТекущий баланс: <b>{u['coins']} 💰</b>{q_txt}", parse_mode="HTML")

@dp.message(F.text == "🗺 Локации")
async def locs(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    ikb = InlineKeyboardBuilder()
    for k, (name, req_lvl, _) in LOCS.items():
        mark = "✅ " if u["loc"] == k else ("🔒 " if u["lvl"] < req_lvl else "")
        ikb.button(text=f"{mark}{name} (Ур.{req_lvl})", callback_data=f"loc_{k}")
    ikb.adjust(2)
    await m.answer(f"🗺 Выбери локацию (твой уровень: <b>{u['lvl']}</b>):", parse_mode="HTML", reply_markup=ikb.as_markup())

@dp.callback_query(F.data.startswith("loc_"))
async def set_loc(c: types.CallbackQuery):
    u = udata(c.from_user.id, c.from_user.first_name)
    k = c.data.split("_", 1)[1]
    if k not in LOCS: return
    name, req_lvl, _ = LOCS[k]
    if u["lvl"] < req_lvl: return await c.answer(f"Нужен {req_lvl} уровень!", show_alert=True)
    u["loc"] = k; save()
    await c.message.edit_text(f"📍 Ты переехал на локацию: <b>{name}</b>", parse_mode="HTML")

@dp.message(F.text == "🏪 Магазин")
async def shop(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    ikb = InlineKeyboardBuilder()
    for rid, (rname, price, mult) in [(r, d) for r, d in RODS.items() if r > u["rod"]][:5]:
        ikb.button(text=f"{rname} (x{mult}) — {price} 💰", callback_data=f"buy_rod_{rid}")
    ikb.button(text="🪱 Черви x10 — 50 💰", callback_data="buy_worms")
    ikb.button(text="✨ Блесна x5 — 150 💰", callback_data="buy_lures")
    ikb.adjust(1)
    await m.answer(f"🏪 <b>Магазин снастей</b>\nТвой баланс: <b>{u['coins']} 💰</b>\nТекущая удочка: <b>{RODS[u['rod']][0]}</b>", parse_mode="HTML", reply_markup=ikb.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def buy(c: types.CallbackQuery):
    u = udata(c.from_user.id, c.from_user.first_name)
    item = c.data[4:]
    if item.startswith("rod_"):
        rid = int(item.split("_")[1])
        if rid <= u["rod"] or rid not in RODS: return await c.answer("Уже куплено!", show_alert=True)
        rname, price, _ = RODS[rid]
        if u["coins"] < price: return await c.answer("Не хватает монет!", show_alert=True)
        u["coins"] -= price; u["rod"] = rid; save()
        return await c.message.edit_text(f"🎉 Куплена новая удочка: <b>{rname}</b>!", parse_mode="HTML")
    elif item == "worms":
        if u["coins"] < 50: return await c.answer("Не хватает монет!", show_alert=True)
        u["coins"] -= 50; u["worms"] += 10; save()
        return await c.answer("Куплено 10 червей! 🪱", show_alert=True)
    elif item == "lures":
        if u["coins"] < 150: return await c.answer("Не хватает монет!", show_alert=True)
        u["coins"] -= 150; u["lures"] += 5; save()
        return await c.answer("Куплено 5 блесен! ✨", show_alert=True)

@dp.message(F.text == "📜 Квесты")
async def quests(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    q = u["quest"]
    title, goal, rc, rxp = QUESTS.get(q["id"], ("Задание", 10, 100, 50))
    ikb = InlineKeyboardBuilder()
    if q.get("done"):
        status = "✅ <b>Выполнено!</b>"
        ikb.button(text="🔄 Взять новый квест", callback_data="new_quest")
    else:
        status = f"Прогресс: <b>{q['prog']} / {goal}</b>"
        ikb.button(text="🔄 Сменить квест (100 💰)", callback_data="reroll_quest")
    await m.answer(f"📜 <b>Текущий квест:</b>\n{title}\n{status}\n🎁 Награда: <b>{rc} 💰</b> и <b>{rxp} XP</b>", parse_mode="HTML", reply_markup=ikb.as_markup())

@dp.callback_query(F.data.in_(("new_quest", "reroll_quest")))
async def change_quest(c: types.CallbackQuery):
    u = udata(c.from_user.id, c.from_user.first_name)
    if c.data == "reroll_quest":
        if u["coins"] < 100: return await c.answer("Нужно 100 💰 для смены!", show_alert=True)
        u["coins"] -= 100
    u["quest"] = new_q(); save()
    title, goal, rc, rxp = QUESTS[u["quest"]["id"]]
    await c.message.edit_text(f"📜 <b>Новый квест:</b>\n{title}\nПрогресс: <b>0 / {goal}</b>\n🎁 Награда: <b>{rc} 💰</b> и <b>{rxp} XP</b>", parse_mode="HTML")

@dp.message(F.text == "📖 Индекс")
async def dex(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    d, ikb = u["dex"], InlineKeyboardBuilder()
    if len(d) >= len(ALL_F) and not u["dd"]: ikb.button(text="🏆 Забрать награду (250000 💰)", callback_data="dex_reward")
    caught = [f"✅ {f} ({d[f]} кг)" for f in ALL_F if f in d]
    preview = "\n".join(caught[-20:]) if caught else "Пока ничего не поймано."
    more = f"\n<i>...и ещё {len(caught)-20} открытых видов</i>" if len(caught) > 20 else ""
    await m.answer(f"📖 <b>Энциклопедия улова: {len(d)} / {len(ALL_F)}</b>\n\nПоследние открытия:\n{preview}{more}", parse_mode="HTML", reply_markup=ikb.as_markup())

@dp.callback_query(F.data == "dex_reward")
async def dex_reward(c: types.CallbackQuery):
    u = udata(c.from_user.id, c.from_user.first_name)
    if len(u["dex"]) >= len(ALL_F) and not u["dd"]:
        u["dd"] = True; u["coins"] += 250000; save()
        await c.message.edit_text("🏆 Поздравляем! Ты собрал весь индекс и получил <b>250 000 💰</b>!", parse_mode="HTML")

@dp.message(F.text == "🎁 Бонус")
async def daily(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    now = time.time()
    if now - u["day"] < 86400:
        left = int(86400 - (now - u["day"]))
        return await m.answer(f"⏳ Бонус будет доступен через <b>{left // 3600}ч {(left % 3600) // 60}м</b>.", parse_mode="HTML")
    u["day"] = now; rew = 150 * u["lvl"]; u["coins"] += rew; u["worms"] += 5; save()
    await m.answer(f"🎁 Ежедневный бонус получен!\n+<b>{rew} 💰</b> и +<b>5 🪱</b>", parse_mode="HTML")

@dp.message(F.text == "🏆 Топ")
async def top(m: types.Message):
    by_coins = sorted(db.values(), key=lambda x: x.get("coins", 0), reverse=True)[:10]
    txt = "🏆 <b>Топ-10 богачей:</b>\n\n" + "\n".join(f"{i}. <b>{p.get('name', 'Рыбак')}</b> (Ур.{p.get('lvl', 1)}) — {p.get('coins', 0)} 💰 | Макс: {p.get('max', 0)}кг" for i, p in enumerate(by_coins, 1))
    await m.answer(txt, parse_mode="HTML")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
