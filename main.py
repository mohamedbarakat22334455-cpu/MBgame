import os, sqlite3, random, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# --- [ الإعدادات ] ---
API_TOKEN = '8663020855:AAHQnGuMmUxXN7sdyw67LfeEDctSAWoW6NE'
WEB_URL = "https://mbgame-production.up.railway.app"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- [ واجهة اللعبة - المحرك القتالي 3D ] ---
async def handle_index(request):
    html = f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>ARMAGEDDON WARZONE</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <style>
            body {{ margin: 0; background: #000; overflow: hidden; font-family: 'Segoe UI', sans-serif; }}
            #ui-layer {{ position: absolute; top: 20px; left: 20px; color: #FFD700; z-index: 10; pointer-events: none; }}
            .stats {{ background: rgba(0,0,0,0.6); padding: 10px; border-radius: 10px; border: 1px solid #FFD700; }}
            
            /* أزرار التحكم */
            .controls {{ position: absolute; bottom: 30px; width: 100%; display: flex; justify-content: space-around; z-index: 20; }}
            .btn-action {{ 
                width: 70px; height: 70px; border-radius: 50%; border: 3px solid #FFD700;
                background: rgba(255,215,0,0.2); color: #FFD700; font-weight: bold; cursor: pointer;
                display: flex; align-items: center; justify-content: center; user-select: none;
            }}
            #fire-btn {{ background: rgba(255,0,0,0.4); border-color: #ff4444; color: #fff; }}
        </style>
    </head>
    <body>
        <div id="ui-layer">
            <div class="stats">
                <div>🏆 اللاعب: {os.environ.get('USER_NAME', 'محمد بركات')}</div>
                <div>🪙 الذهب: <span id="gold-val">100</span></div>
            </div>
        </div>

        <div class="controls">
            <div class="btn-action" id="move-btn">MOVE</div>
            <div class="btn-action" id="fire-btn">FIRE 🔥</div>
        </div>

        <script>
            // إعداد المشهد 3D
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x050505);
            scene.fog = new THREE.Fog(0x050505, 1, 50);

            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);

            // إضاءة النيون
            const ambientLight = new THREE.AmbientLight(0x404040, 2);
            scene.add(ambientLight);
            const sun = new THREE.DirectionalLight(0xFFD700, 1);
            sun.position.set(5, 10, 7);
            scene.add(sun);

            // إنشاء المحارب (جسم بشري مبسط)
            const playerGroup = new THREE.Group();
            const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.4, 1, 4, 8), new THREE.MeshStandardMaterial({{color: 0xFFD700}}));
            const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 16), new THREE.MeshStandardMaterial({{color: 0xFFD700}}));
            head.position.y = 0.8;
            playerGroup.add(body, head);
            scene.add(playerGroup);

            // الأرضية (Cyber Grid)
            const grid = new THREE.GridHelper(100, 40, 0xFFD700, 0x222222);
            scene.add(grid);

            camera.position.set(0, 3, 6);
            camera.lookAt(playerGroup.position);

            // نظام الحركة والضرب
            let isMoving = false;
            document.getElementById('move-btn').ontouchstart = () => isMoving = true;
            document.getElementById('move-btn').ontouchend = () => isMoving = false;

            document.getElementById('fire-btn').onclick = () => {{
                // تأثير ضرب النار
                const bullet = new THREE.Mesh(new THREE.SphereGeometry(0.1), new THREE.MeshBasicMaterial({{color: 0xff0000}}));
                bullet.position.set(playerGroup.position.x, 0.5, playerGroup.position.z);
                scene.add(bullet);
                setTimeout(() => scene.remove(bullet), 500);
            }};

            function animate() {{
                requestAnimationFrame(animate);
                if(isMoving) playerGroup.position.z -= 0.1;
                renderer.render(scene, camera);
            }}
            animate();
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def handle_api(request):
    return web.json_response({'status': 'ok'})

@dp.message(Command("start"))
async def start(m: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⚔️ دخول Warzone 3D", web_app=types.WebAppInfo(url=WEB_URL))]
    ])
    await m.answer(f"🚀 **أرمجدون: باتل رويال** جاهزة يا **{m.from_user.first_name}**\n\nاللعبة دلوقتي فيها حركة وجرافيك حقيقي. ادخل جرب!", reply_markup=kb)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/api/play', handle_api)
    runner = web.AppRunner(app); await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start(); await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
