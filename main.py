import os, asyncio, random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ محرك الحرب العالمية 3D ] ---
async def handle_index(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON: EXTINCTION</title>
        <script src="https://cdn.babylonjs.com/babylon.js"></script>
        <style>
            body { margin: 0; background: #000; overflow: hidden; font-family: 'Courier New', monospace; }
            #renderCanvas { width: 100%; height: 100%; touch-action: none; }
            .hud { position: absolute; top: 15px; left: 15px; color: #0f0; text-shadow: 0 0 5px #0f0; pointer-events: none; z-index: 10; }
            .controls { position: absolute; bottom: 30px; width: 100%; display: flex; justify-content: space-around; z-index: 20; }
            .btn { width: 80px; height: 80px; border-radius: 50%; border: 4px solid #FFD700; background: rgba(0,0,0,0.5); color: #FFD700; font-weight: bold; display: flex; align-items: center; justify-content: center; font-size: 1.2em; box-shadow: 0 0 15px #FFD700; }
            #fire { border-color: #f00; color: #f00; box-shadow: 0 0 15px #f00; }
        </style>
    </head>
    <body>
        <div class="hud">
            HP: <span id="hp">100</span>% | GOLD: <span id="gold">0</span><br>
            MISSION: 💀 SURVIVE THE NIGHT
        </div>
        <canvas id="renderCanvas"></canvas>
        <div class="controls">
            <div class="btn" id="move">RUN</div>
            <div class="btn" id="fire">FIRE</div>
        </div>

        <script>
            const canvas = document.getElementById("renderCanvas");
            const engine = new BABYLON.Engine(canvas, true);

            const createScene = function() {
                const scene = new BABYLON.Scene(engine);
                scene.clearColor = new BABYLON.Color3(0, 0, 0);
                
                // إضافة ضباب (Atmosphere)
                scene.fogMode = BABYLON.Scene.FOGMODE_EXP;
                scene.fogDensity = 0.05;
                scene.fogColor = new BABYLON.Color3(0, 0, 0);

                const camera = new BABYLON.FreeCamera("camera1", new BABYLON.Vector3(0, 5, -10), scene);
                camera.setTarget(BABYLON.Vector3.Zero());

                const light = new BABYLON.PointLight("spark", new BABYLON.Vector3(0, 10, 0), scene);
                light.diffuse = new BABYLON.Color3(1, 0.8, 0);

                // اللاعب (شخصية متطورة)
                const player = BABYLON.MeshBuilder.CreateCapsule("player", {height: 2, radius: 0.5}, scene);
                player.position.y = 1;
                const pMat = new BABYLON.StandardMaterial("pm", scene);
                pMat.emissiveColor = new BABYLON.Color3(1, 0.84, 0);
                player.material = pMat;

                // الأرضية (ساحة حرب ليزر)
                const ground = BABYLON.MeshBuilder.CreateGround("gd", {width: 200, height: 200}, scene);
                const gMat = new BABYLON.StandardMaterial("gm", scene);
                gMat.wireframe = true;
                gMat.emissiveColor = new BABYLON.Color3(0, 0.2, 0);
                ground.material = gMat;

                // نظام الزومبي (AI)
                const zombies = [];
                for(let i=0; i<10; i++) {
                    let z = BABYLON.MeshBuilder.CreateBox("z", {size: 1.5}, scene);
                    z.position.set(Math.random()*60-30, 0.75, Math.random()*60-30);
                    let zMat = new BABYLON.StandardMaterial("zm", scene);
                    zMat.diffuseColor = new BABYLON.Color3(1, 0, 0);
                    z.material = zMat;
                    zombies.push(z);
                }

                // الحركة والضرب
                let isMoving = false;
                document.getElementById('move').onpointerdown = () => isMoving = true;
                document.getElementById('move').onpointerup = () => isMoving = false;
                
                document.getElementById('fire').onclick = () => {
                    const shot = BABYLON.MeshBuilder.CreateSphere("s", {diameter: 0.2}, scene);
                    shot.position = player.position.clone();
                    shot.position.y += 0.5;
                    const sMat = new BABYLON.StandardMaterial("sm", scene);
                    sMat.emissiveColor = new BABYLON.Color3(1, 1, 0);
                    shot.material = sMat;
                    
                    // تحريك الرصاصة
                    let frame = 0;
                    scene.registerBeforeRender(() => {
                        if(frame < 20) { shot.position.z += 1; frame++; }
                        else { shot.dispose(); }
                    });
                };

                scene.registerBeforeRender(() => {
                    if(isMoving) {
                        player.position.z += 0.2;
                        camera.position.z = player.position.z - 10;
                    }
                    // مطاردة الزومبي
                    zombies.forEach(z => {
                        let dir = player.position.subtract(z.position).normalize();
                        z.position.addInPlace(dir.scale(0.04));
                    });
                });

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
        [types.InlineKeyboardButton(text="💀 دخول ساحة الإبادة (3D)", web_app=types.WebAppInfo(url=WEB_URL))]
    ])
    await m.answer(f"🔥 **أهلاً بك في الجحيم يا محمد!**\n\nاللعبة اتطورت 180 درجة:\n✅ 10 وحوش بيطاردوك بذكاء اصطناعي.\n✅ نظام إطلاق نار حقيقي وتأثيرات ضوئية.\n✅ جرافيك ضبابي مرعب (Fog System).\n✅ تحكم أسرع وأخف.\n\nادخل الساحة وحاول تعيش!", reply_markup=kb)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start(); await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
