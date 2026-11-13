# main.py
# นำเข้าไลบรารีที่จำเป็น
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import GPUtil as GPU
import time
import os
import sys # เพิ่มไลบรารี sys เพื่อตรวจสอบ virtual environment

# ฟังก์ชันสำหรับบังคับใช้ virtual environment
def enforce_virtual_environment():
    """
    ตรวจสอบว่าโปรแกรมกำลังทำงานใน virtual environment หรือไม่
    หากไม่อยู่ จะแสดงคำสั่งเพื่อเปิดใช้งานและหยุดการทำงานของโปรแกรม
    """
    # ตรวจสอบว่า virtual environment ถูกเปิดใช้งานอยู่หรือไม่
    if sys.prefix == sys.base_prefix:
        print("Virtual environment is not activated.")
        print("Please activate it before running this script.")
        
        # แสดงคำสั่งที่เหมาะสมสำหรับระบบปฏิบัติการ
        if os.name == 'nt':  # สำหรับ Windows
            activate_command = r"venv\Scripts\activate"
        else:  # สำหรับ macOS และ Linux
            activate_command = "source venv/bin/activate"
            
        print(f"Run the following command:")
        print(f"    {activate_command}")
        
        # หยุดการทำงานของโปรแกรม
        sys.exit(1)

# บังคับใช้ virtual environment ก่อนที่จะเริ่มต้นแอปพลิเคชัน
enforce_virtual_environment()

# สร้างอินสแตนซ์ของ FastAPI
app = FastAPI()

# ตั้งค่าไดเรกทอรีสำหรับเทมเพลต Jinja2
# ตรวจสอบว่าไดเรกทอรี 'templates' มีอยู่หรือไม่
template_dir = "templates"
if not os.path.exists(template_dir):
    os.makedirs(template_dir)
    print(f"Directory '{template_dir}' created.")

templates = Jinja2Templates(directory=template_dir)

# ฟังก์ชันสำหรับดึงข้อมูล GPU แบบเรียลไทม์
def get_realtime_gpu_info():
    """
    ดึงข้อมูลสถานะ GPU แบบเรียลไทม์และจัดรูปแบบเป็น list of dictionaries.
    """
    try:
        # ดึงข้อมูล GPU ทั้งหมด
        gpus = GPU.getGPUs()
        gpu_data = []
        # วนลูปเพื่อจัดรูปแบบข้อมูลของ GPU แต่ละตัว
        for gpu in gpus:
            gpu_data.append({
                'id': gpu.id,
                'name': gpu.name,
                'load_percent': f'{gpu.load*100:.2f}',
                'load_raw': gpu.load * 100,
                'memory_used': f'{gpu.memoryUsed:.2f}',
                'memory_total': f'{gpu.memoryTotal:.2f}',
                'memory_util_percent': f'{gpu.memoryUtil*100:.2f}',
                'memory_util_raw': gpu.memoryUtil * 100,
                'temperature': f'{gpu.temperature:.0f}',
                'temperature_raw': gpu.temperature # เพิ่มค่าอุณหภูมิแบบดิบ
            })
        return gpu_data
    except Exception as e:
        # คืนค่าข้อผิดพลาดหากไม่สามารถดึงข้อมูลได้
        return [{'error': str(e)}]

# สร้าง API endpoint สำหรับข้อมูล GPU
@app.get("/api/gpu")
async def api_gpu_info():
    """
    API endpoint ที่ส่งคืนข้อมูล GPU ในรูปแบบ JSON
    """
    return get_realtime_gpu_info()

# สร้าง route หลักสำหรับแสดงหน้าเว็บ
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    แสดงหน้าเว็บหลัก (index.html) พร้อมข้อมูล GPU
    """
    gpu_info = get_realtime_gpu_info()
    return templates.TemplateResponse("index.html", {"request": request, "gpus": gpu_info})

# ส่วนของโค้ด HTML ที่ต้องบันทึกเป็นไฟล์ templates/index.html

# Note: The following HTML code must be saved as 'templates/index.html'

```html
<!-- templates/index.html -->
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPU Monitor</title>
    <script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background-color: #1e293b; /* slate-800 */
            color: #f1f5f9; /* slate-100 */
        }
        .container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 2rem;
        }
        .card {
            background-color: #334155; /* slate-700 */
            border-radius: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .progress-bar {
            height: 1.5rem;
            border-radius: 9999px;
            background-color: #475569; /* slate-600 */
        }
        .progress-fill {
            height: 100%;
            border-radius: 9999px;
            transition: width 0.5s ease-in-out;
        }
        .gradient-bg {
            background-image: linear-gradient(to right, #6b21a8, #c026d3); /* purple-800 to fuchsia-600 */
        }
        .glow-effect {
            box-shadow: 0 0 20px rgba(192, 38, 211, 0.5);
        }
    </style>
</head>
<body class="bg-slate-900 text-slate-100">
    <div class="container mx-auto p-8 md:p-12 lg:p-16">
        <h1 class="text-4xl md:text-5xl font-bold text-center mb-12 text-purple-400 drop-shadow-lg">
            GPU Monitor Dashboard
        </h1>

        <div id="gpu-container" class="space-y-8">
            {% if gpus %}
                {% for gpu in gpus %}
                    <div class="card p-6 md:p-8 glow-effect">
                        <h2 class="text-2xl font-semibold mb-4 text-purple-300">
                            {{ gpu.name }} (ID: {{ gpu.id }})
                        </h2>

                        <div class="space-y-6">
                            <!-- GPU Load Section -->
                            <div>
                                <div class="flex justify-between items-center mb-2">
                                    <span class="font-medium text-slate-300">GPU Load</span>
                                    <span class="font-semibold text-purple-400" id="load-{{ gpu.id }}">{{ gpu.load_percent }}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill gradient-bg" id="load-bar-{{ gpu.id }}" style="width: {{ gpu.load_percent }}%;"></div>
                                </div>
                            </div>

                            <!-- GPU Memory Utilization Section -->
                            <div>
                                <div class="flex justify-between items-center mb-2">
                                    <span class="font-medium text-slate-300">Memory Utilization</span>
                                    <span class="font-semibold text-purple-400" id="memory-util-{{ gpu.id }}">{{ gpu.memory_util_percent }}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill gradient-bg" id="memory-util-bar-{{ gpu.id }}" style="width: {{ gpu.memory_util_percent }}%;"></div>
                                </div>
                                <div class="text-sm text-slate-400 mt-2">
                                    ใช้: <span id="memory-used-{{ gpu.id }}">{{ gpu.memory_used }}</span> MB / ทั้งหมด: <span id="memory-total-{{ gpu.id }}">{{ gpu.memory_total }}</span> MB
                                </div>
                            </div>

                            <!-- GPU Temperature Section -->
                            <div>
                                <div class="flex justify-between items-center mb-2">
                                    <span class="font-medium text-slate-300">Temperature</span>
                                    <span class="font-semibold text-purple-400" id="temp-{{ gpu.id }}">{{ gpu.temperature }}°C</span>
                                </div>
                            </div>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="text-center text-red-400">
                    ไม่พบข้อมูล GPU หรือเกิดข้อผิดพลาดในการดึงข้อมูล
                </div>
            {% endif %}
        </div>
    </div>

    <script>
        // ฟังก์ชันสำหรับอัปเดตข้อมูล GPU
        async function updateGpuInfo() {
            try {
                const response = await fetch('/api/gpu');
                const gpus = await response.json();

                if (gpus.length === 0 || gpus[0].error) {
                    document.getElementById('gpu-container').innerHTML = `
                        <div class="text-center text-red-400">
                            ไม่พบข้อมูล GPU หรือเกิดข้อผิดพลาด: ${gpus[0]?.error || 'ไม่สามารถดึงข้อมูลได้'}
                        </div>
                    `;
                    return;
                }

                gpus.forEach(gpu => {
                    const id = gpu.id;

                    // Update Load
                    const loadPercent = gpu.load_percent;
                    document.getElementById(`load-${id}`).innerText = `${loadPercent}%`;
                    document.getElementById(`load-bar-${id}`).style.width = `${loadPercent}%`;

                    // Update Memory Utilization
                    const memUtilPercent = gpu.memory_util_percent;
                    document.getElementById(`memory-util-${id}`).innerText = `${memUtilPercent}%`;
                    document.getElementById(`memory-util-bar-${id}`).style.width = `${memUtilPercent}%`;
                    document.getElementById(`memory-used-${id}`).innerText = gpu.memory_used;
                    document.getElementById(`memory-total-${id}`).innerText = gpu.memory_total;

                    // Update Temperature
                    document.getElementById(`temp-${id}`).innerText = `${gpu.temperature}°C`;
                });

            } catch (error) {
                console.error("Error fetching GPU data:", error);
                document.getElementById('gpu-container').innerHTML = `
                    <div class="text-center text-red-400">
                        เกิดข้อผิดพลาดในการดึงข้อมูล GPU
                    </div>
                `;
            }
        }

        // อัปเดตข้อมูลทุกๆ 3 วินาที
        setInterval(updateGpuInfo, 3000);
    </script>
</body>
</html>
