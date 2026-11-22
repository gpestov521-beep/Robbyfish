import asyncio, json, os, random, time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

TOKEN = "9262073471:AAGn1POkp2i51s0mOhRyI97AC83JhjV8bzM"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fishing_db.json")
bot = Bot(token=TOKEN, session=AiohttpSession(proxy="http://proxy.server:3128"))
dp = Dispatcher()
db = json.load(open(DB, encoding="utf-8")) if os.path.exists(DB) else {}

def save():
    with open(DB, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False)

RODS = {1: ("🎋 Бамбук", 0, 1.0), 2: ("🎣 Спиннинг", 150, 1.5), 3: ("⚡ Карбон", 600, 2.2), 4: ("🛡️ Титан", 1800, 3.2), 5: ("👑 Легенда", 5000, 4.5), 6: ("🔱 Трезубец", 15000, 6.5)}
LOCS = {
    "pond": ("🏞 Пруд", 1, (("👢 Сапог", 1, 2, 20), ("🐟 Карась", 12, 5, 45), ("🐠 Окунь", 18, 8, 25), ("🐸 Лягушка", 25, 12, 10))),
    "river": ("🌊 Река", 2, (("🐟 Плотва", 25, 10, 40), ("🦈 Щука", 65, 20, 35), ("🐊 Судак", 80, 25, 20), ("🐳 Сом", 160, 45, 5))),
    "lake": ("🏔 Озеро", 3, (("🐟 Форель", 90, 30, 40), ("🐠 Хариус", 130, 40, 30), ("🐡 Налим", 180, 55, 20), ("👑 Осетр", 400, 100, 10))),
    "ocean": ("🚢 Океан", 4, (("🐡 Фугу", 150, 45, 35), ("🍣 Тунец", 300, 75, 35), ("🦈 Акула", 750, 140, 20), ("👑 Марлин", 1600, 250, 10))),
    "abyss": ("🌋 Бездна", 5, (("🦑 Кальмар", 500, 120, 40), ("🐉 Удильщик", 1200, 220, 30), ("🦖 Мегалодон", 3000, 450, 20), ("🐙 Кракен", 7000, 900, 10)))
}
QUESTS = {"catch_10": ("Поймать 10 рыб", 10, 200, 80), "catch_25": ("Поймать 25 рыб", 25, 550, 200), "weight_50": ("Наловить 50 кг", 50, 400, 150), "sell_500": ("Продать на 500 💰", 500, 350, 120)}
ALL_F = [n for _, _, p in LOCS.values() for n, _, _, _ in p]

def new_q(): return {"id": random.choice(list(QUESTS)), "prog": 0, "done": False}
def udata(uid, name="Рыбак"):
    u = db.setdefault(str(uid), {"name": name, "coins": 0, "rod": 1, "loc": "pond", "bag": [], "worms": 0, "lures": 0, "cd": 0, "day": 0, "max": 0.0, "lvl": 1, "xp": 0, "quest": new_q(), "dex": {}, "dd": False})
    u["name"] = str(name).replace("<", "").replace(">", ""); u.setdefault("lvl", 1); u.setdefault("xp", 0); u.setdefault("dex", {}); u.setdefault("dd", False)
    if not isinstance(u.get("quest"), dict): u["quest"] = new_q()
    return u

def add_xp(u, amt):
    u["xp"] += amt; msg = ""
    while u["xp"] >= u["lvl"] * 100: u["xp"] -= u["lvl"] * 100; u["lvl"] += 1; msg += f"\n🎊 <b>УРОВЕНЬ {u['lvl']}!</b>"
    return msg

def upd_q(u, qt, val):
    q = u["quest"]
    if q.get("done") or not q.get("id", "").startswith(qt): return ""
    _, g, rc, rxp = QUESTS.get(q["id"], ("", 10, 100, 50)); q["prog"] = round(q["prog"] + val, 2)
    if q["prog"] >= g: q["prog"], q["done"], u["coins"] = g, True, u["coins"] + rc; return f"\n✅ <b>КВЕСТ!</b> +{rc} 💰, +{rxp} XP" + add_xp(u, rxp)
    return ""

def kb():
    b = ReplyKeyboardBuilder()
    for t in ("🎣 Закинуть", "🎒 Садок", "🗺 Локации", "🏪 Магазин", "📜 Квесты", "📖 Индекс", "🎁 Бонус", "🏆 Топ"): b.button(text=t)
    return b.adjust(2).as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start(m: types.Message): udata(m.from_user.id, m.from_user.first_name); save(); await m.answer("Привет, рыбак! 🌊", reply_markup=kb())

@dp.message(F.text == "🎣 Закинуть")
async def fish(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name)
    if time.time() - u["cd"] < 4: return await m.answer(f"⏳ Ждите {round(4 - (time.time() - u['cd']), 1)}с.")
    u["cd"] = time.time(); ln, _, pool = LOCS.get(u["loc"], LOCS["pond"]); _, _, ml = RODS.get(u["rod"], RODS.get(1))
    bm, bt = (1.5, "✨") if u["lures"] > 0 else ((1.2, "🪱") if u["worms"] > 0 else (1.0, "🪝"))
    if u["lures"] > 0: u["lures"] -= 1
    elif u["worms"] > 0: u["worms"] -= 1
    ch_txt = ""
    if random.randint(1, 10) == 1: c = random.randint(50, 300) * u["lvl"]; u["coins"] += c; ch_txt = f"\n💎 <b>Сундук: +{c} 💰!</b>"
    r, cur, fn, bp, bxp = random.uniform(0, sum(c for _, _, _, c in pool)), 0, "🐟 Карась", 10, 5
    for n, p, xp, c in pool:
        if cur + c >= r: fn, bp, bxp = n, p, xp; break
        cur += c
    w, pr, xpg = round(random.uniform(0.5, 5.0) * ml * bm, 2), int(bp * ml * bm), int(bxp * bm)
    u["bag"].append((fn, w, pr)); u["max"] = max(u["max"], w)
    nd = f"\n🆕 <b>Индекс: {len(u['dex'])+1}/{len(ALL_F)}!</b>" if fn not in u["dex"] else ""
    u["dex"][fn] = max(u["dex"].get(fn, 0), w)
    ext = add_xp(u, xpg) + upd_q(u, "catch", 1) + upd_q(u, "weight", w); save()
    await m.answer(f"📍 {ln} {bt}{ch_txt}\n🎉 <b>{fn}</b> | ⚖️ {w}кг | 💵 {pr}💰 | ⭐ +{xpg}XP{nd}{ext}", parse_mode="HTML", reply_markup=kb())
@dp.message(F.text == "📖 Индекс")
async def dex(m: types.Message):
    u = udata(m.from_user.id); d = u["dex"]; ikb = InlineKeyboardBuilder()
    if len(d) >= len(ALL_F) and not u["dd"]: ikb.button(text="🏆 Награда (10000 💰)", callback_data="dr")
    txt = f"📖 <b>Индекс ({len(d)}/{len(ALL_F)}):</b>\n" + "\n".join(f"<b>{ln}:</b> " + ", ".join(f"{fn}({d[fn]}кг)" if fn in d else "❓" for fn, _, _, _ in p) for ln, _, p in LOCS.values())
    await m.answer(txt, reply_markup=ikb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "dr")
async def dr(c: types.CallbackQuery):
    u = udata(c.from_user.id)
    if len(u["dex"]) < len(ALL_F) or u["dd"]: return await c.answer("Рано!", show_alert=True)
    u["dd"], u["coins"] = True, u["coins"] + 10000; ext = add_xp(u, 1000); save()
    await c.message.answer(f"🏆 <b>ИНДЕКС СОБРАН!</b> +10000 💰, +1000 XP{ext}", parse_mode="HTML"); await c.answer()

@dp.message(F.text == "🎒 Садок")
async def bag(m: types.Message):
    u = udata(m.from_user.id, m.from_user.first_name); rn, _, _ = RODS.get(u["rod"], RODS.get(1)); val = sum(p for _, _, p in u["bag"]); ikb = InlineKeyboardBuilder()
    if u["bag"]: ikb.button(text=f"💰 Продать (+{val})", callback_data="sell")
    await m.answer(f"👤 <b>{u['name']}</b> (ID: <code>{m.from_user.id}</code>)\n⭐ Ур.{u['lvl']} ({u['xp']}/{u['lvl']*100}XP) | 💰 {u['coins']}\n🎣 {rn} | 🪱 {u['worms']} | ✨ {u['lures']}\n📖 {len(u['dex'])}/{len(ALL_F)} | 🏆 {u['max']}кг | 🧺 {len(u['bag'])}шт ({val}💰)", reply_markup=ikb.as_markup(), parse_mode="HTML")

@dp.callback_query(F.data == "sell")
async def sell(c: types.CallbackQuery):
    u = udata(c.from_user.id)
    if not u["bag"]: return await c.answer("Пусто!", show_alert=True)
    val = sum(p for _, _, p in u["bag"]); u["coins"] += val; u["bag"].clear(); qm = upd_q(u, "sell", val); save()
    await c.message.answer(f"✅ +{val} 💰! Баланс: {u['coins']}{qm}", parse_mode="HTML"); await c.answer()

@dp.message(F.text == "📜 Квесты")
async def quests(m: types.Message):
    u = udata(m.from_user.id); q = u["quest"]; desc, g, rc, rxp = QUESTS.get(q["id"], ("", 10, 100, 50)); ikb = InlineKeyboardBuilder()
    if q["done"]: ikb.button(text="🔄 Новый квест", callback_data="nq")
    prog = q["prog"]
    st = "✅ Готово!" if q["done"] else f"⏳ {prog}/{g}"
    await m.answer(f"📜 {desc}\n{st}\n🎁 {rc} 💰, {rxp} XP", reply_markup=ikb.as_markup())

@dp.callback_query(F.data == "nq")
async def nq(c: types.CallbackQuery):
    u = udata(c.from_user.id)
    if not u["quest"].get("done"): return await c.answer("Выполните текущий!", show_alert=True)
    u["quest"] = new_q(); save(); desc, g, rc, rxp = QUESTS.get(u["quest"]["id"])
    await c.message.answer(f"🆕 {desc} (0/{g}) | {rc} 💰, {rxp} XP"); await c.answer()

@dp.message(F.text == "🗺 Локации")
async def locs(m: types.Message):
    u = udata(m.from_user.id); ikb = InlineKeyboardBuilder()
    for k, (n, rl, _) in LOCS.items(): ikb.button(text=f"{'✅' if u['loc']==k else ('🔒' if u['lvl']<rl else '🌊')} {n} ({rl} ур.)", callback_data=f"l_{k}")
    await m.answer("Водоемы:", reply_markup=ikb.adjust(1).as_markup())

@dp.callback_query(F.data.startswith("l_"))
async def set_loc(c: types.CallbackQuery):
    u = udata(c.from_user.id); k = c.data.replace("l_", ""); n, rl, _ = LOCS.get(k)
    if u["lvl"] < rl: return await c.answer(f"Нужен {rl} ур.!", show_alert=True)
    u["loc"] = k; save(); await c.message.answer(f"🚶 Локация: {n}"); await c.answer()

@dp.message(F.text == "🏪 Магазин")
async def shop(m: types.Message):
    u = udata(m.from_user.id); ikb = InlineKeyboardBuilder()
    for lvl, (n, p, ml) in RODS.items():
        if lvl == u["rod"] + 1: ikb.button(text=f"🎣 {n} x{ml} ({p} 💰)", callback_data=f"r_{lvl}")
    ikb.button(text="🪱 Черви 10шт (50 💰)", callback_data="b_w"); ikb.button(text="✨ Блесна 10шт (150 💰)", callback_data="b_l")
    await m.answer(f"🏪 Баланс: {u['coins']} 💰", reply_markup=ikb.adjust(1).as_markup())

@dp.callback_query(F.data.startswith(("r_", "b_")))
async def buy(c: types.CallbackQuery):
    u = udata(c.from_user.id)
    if c.data.startswith("r_"):
        lvl = int(c.data.replace("r_", "")); n, p, _ = RODS.get(lvl)
        if u["coins"] < p: return await c.answer("Мало монет!", show_alert=True)
        u["coins"] -= p; u["rod"] = lvl; msg = f"🎉 Куплено: {n}!"
    else:
        p, k, msg = (50, "worms", "🪱 +10 червей!") if c.data == "b_w" else (150, "lures", "✨ +10 блесен!")
        if u["coins"] < p: return await c.answer("Мало монет!", show_alert=True)
        u["coins"] -= p; u[k] += 10
    save(); await c.message.answer(msg); await c.answer()

@dp.message(F.text == "🎁 Бонус")
async def bonus(m: types.Message):
    u = udata(m.from_user.id)
    if time.time() - u["day"] < 86400: return await m.answer("⏳ Раз в 24 часа!")
    rew = random.randint(100, 300) * u["lvl"]; u["coins"] += rew; u["day"] = time.time(); save()
    await m.answer(f"🎁 Бонус: +{rew} 💰!")

@dp.message(Command("pay"))
async def pay(m: types.Message):
    p = m.text.split()
    if len(p) != 3 or not p.pop().isdigit(): return await m.answer("Пример: /pay ID сумма")
    amt, tid = int(m.text.split().pop()), m.text.split().pop(1); u = udata(m.from_user.id)
    if tid not in db or u["coins"] < amt or amt <= 0: return await m.answer("❌ Ошибка.")
    u["coins"] -= amt; db[tid]["coins"] += amt; save(); await m.answer(f"💸 Переведено {amt} 💰 -> {db[tid]['name']}")

@dp.message(F.text == "🏆 Топ")
async def top(m: types.Message):
    lines = [f"{i}. <b>{x['name']}</b> [Ур.{x.get('lvl',1)}] — {x['coins']} 💰" for i, x in enumerate(sorted(db.values(), key=lambda z: (z.get("lvl", 1), z["coins"]), reverse=True)[:10], 1)]
    await m.answer("🏆 <b>Топ:</b>\n" + ("\n".join(lines) if lines else "Пусто"), parse_mode="HTML")

@dp.message()
async def any_msg(m: types.Message): await m.answer("Меню 👇", reply_markup=kb())

if __name__ == "__main__": asyncio.run(dp.start_polling(bot))
