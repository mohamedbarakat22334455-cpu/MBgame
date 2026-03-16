import os, asyncio, random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ واجهة اللعبة - المحرك القتالي الكامل ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON WARZONE</title>
        <script src="https://cdn.babylonjs.com/babylon.js"></script>
        <style>
            body { margin: 0; background: #000; overflow: hidden; font-family: 'Segoe UI', sans-serif; }
            #renderCanvas { width: 100%; height: 100%; outline: none; }
            .hud { position: absolute; top: 10px; left: 10px; color: #FFD700; background: rgba(0,0,0,0.7); padding: 10px; border: 1px solid #FFD700; border-radius: 10px; z-index: 10; pointer-events: none; }
            .controls { position: absolute; bottom: 30px; width: 100%; display: flex; justify-content: space-around; z-index: 20; }
            .joy { width: 80px; height: 80px; border: 4px solid #FFD700; border-radius: 50%; background: rgba(255,215,0,0.1); color: #FFD700; font-weight: bold; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px #FFD700; }
            #fire { border-color: #f00; color: #f00; box-shadow: 0 0 15px #f00; }
        </style>
    </head>
    <body>
        <div class="hud">
            👤 اللاعب: محمد بركات <br>
            🪙 الذهب: <span id="gold">500</span> | 🩸 HP: <span id="hp">100</span>
        </div>
        <canvas id="renderCanvas"></canvas>
        <div class="controls">
            <div class="joy" id="move">RUN 🏃‍♂️</div>
            <div class="joy" id="fire">FIRE 🔥</div>
        </div>

        <script>
            const canvas = document.getElementById("renderCanvas");
            const engine = new BABYLON.Engine(canvas, true);

            const createScene = function() {
                const scene = new BABYLON.Scene(engine);
                scene.clearColor = new BABYLON.Color3(0, 0, 0);

                const camera = new BABYLON.ArcRotateCamera("cam", -Math.PI/2, Math.PI/3, 15, BABYLON.Vector3.Zero(), scene);
                camera.attachControl(canvas, true);

                // إضاءة نيون ذهبية
                const light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0, 1, 0), scene);
                light.intensity = 0.6;
                const glow = new BABYLON.GlowLayer("glow", scene);
                glow.intensity = 1.0;

                // المحارب (بشكل بشري متطور)
                const player = BABYLON.MeshBuilder.CreateCapsule("p", {height: 2, radius: 0.5}, scene);
                player.position.y = 1;
                const pMat = new BABYLON.StandardMaterial("pm", scene);
                pMat.emissiveColor = new BABYLON.Color3(1, 0.84, 0);
                player.material = pMat;

                // الوحوش (Zombies)
                const bots = [];
                for(let i=0; i<6; i++) {
                    let bot = BABYLON.MeshBuilder.CreateBox("b", {size: 1.5}, scene);
                    bot.position.set(randomRange(-20, 20), 0.75, randomRange(-20, 20));
                    let bMat = new BABYLON.StandardMaterial("bm", scene);
                    bMat.diffuseColor = new BABYLON.Color3(1, 0, 0);
                    bot.material = bMat;
                    bots.push(bot);
                }

                // نظام الطلقات
                const shoot = () => {
                    const bullet = BABYLON.MeshBuilder.CreateSphere("s", {diameter: 0.3}, scene);
                    bullet.position = player.position.clone();
                    bullet.position.y += 0.5;
                    const bMat = new BABYLON.StandardMaterial("bm", scene);
                    bMat.emissiveColor = new BABYLON.Color3(1, 0, 0);
                    bullet.material = bMat;
                    
                    let dist = 0;
                    scene.onBeforeRenderObservable.add(() => {
                        if(dist < 30) { bullet.position.z += 1; dist++; }
                        else { bullet.dispose(); }
                    });
                };

                // تحكم
                let isMoving = false;
                document.getElementById('move').onpointerdown = () => isMoving = true;
                document.getElementById('move').onpointerup = () => isMoving = false;
                document.getElementById('fire').onclick = shoot;

                scene.registerBeforeRender(() => {
                    if(isMoving) { player.position.z += 0.15; camera.target = player.position; }
                    bots.forEach(b => {
                        let dir = player.position.subtract(b.position).normalize();
                        b.position.addInPlace(dir.scale(0.03)); // الوحوش بتطاردك
                    });
                });

                function randomRange(min, max) { return Math.random() * (max - min) + min; }
                return scene;
            };

            const scene = createScene();
            engine.runRenderLoop(() => scene.render());
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔱 دخول حرب أرمجدون (Full Game)", web_app=types.WebAppInfo(url=WEB_URL))]
    ])
    await m.answer(f"🚀 **النسخة الكاملة جاهزة يا محمد!**\n\nأضفت لك:\n✅ نظام إطلاق نار حقيقي (Bullets).\n✅ وحوش ذكية بتطاردك بجد.\n✅ جرافيك نيون ذهبي بيلمع (Glow).\n✅ تحكم Joystick أسرع.\n\nادخل الساحة دلوقتي وورينا مهارتك!", reply_markup=kb)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start(); await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
