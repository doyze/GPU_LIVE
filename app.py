# นำเข้าไลบรารีที่จำเป็น
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import GPUtil as GPU
import os
import pwd
import subprocess
import time

# สร้างอินสแตนซ์ของ FastAPI
app = FastAPI()

# ตั้งค่าไดเรกทอรีสำหรับเทมเพลต Jinja2
templates = Jinja2Templates(directory="templates")

MAX_COMMAND_LENGTH = 80

# อ่านรายละเอียดของ process จาก /proc (อ่านข้าม user ได้)
def get_process_detail(pid):
    user = pwd.getpwuid(os.stat(f"/proc/{pid}").st_uid).pw_name
    with open(f"/proc/{pid}/cmdline", "rb") as f:
        command = f.read().replace(b"\0", b" ").decode(errors="replace").strip()
    if not command:
        # process ที่ตั้งชื่อเอง (เช่น VLLM::Worker) จะไม่มี cmdline ให้อ่าน
        with open(f"/proc/{pid}/comm") as f:
            command = f.read().strip()
    if len(command) > MAX_COMMAND_LENGTH:
        command = command[:MAX_COMMAND_LENGTH] + "…"
    return user, command

# ดึงรายการ process ที่ใช้ GPU แต่ละใบผ่าน nvidia-smi
def get_gpu_processes():
    uuid_to_index = {}
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=10,
    ).stdout
    for line in out.strip().splitlines():
        index, uuid = [x.strip() for x in line.split(",")]
        uuid_to_index[uuid] = int(index)

    processes = {}
    out = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10,
    ).stdout
    for line in out.strip().splitlines():
        if not line.strip():
            continue
        try:
            uuid, pid, memory = [x.strip() for x in line.split(",")]
            user, command = get_process_detail(int(pid))
            processes.setdefault(uuid_to_index[uuid], []).append({
                "pid": int(pid),
                "user": user,
                "command": command,
                "memory_mb": int(memory),
            })
        except (OSError, ValueError, KeyError):
            # process อาจตายไประหว่างอ่าน /proc
            continue
    for plist in processes.values():
        plist.sort(key=lambda p: p["memory_mb"], reverse=True)
    return processes

# ฟังก์ชันสำหรับดึงข้อมูล GPU แบบเรียลไทม์
def get_realtime_gpu_info():
    try:
        # ดึงข้อมูล GPU ทั้งหมด
        gpus = GPU.getGPUs()
        try:
            gpu_processes = get_gpu_processes()
        except Exception:
            gpu_processes = {}
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
                'temperature_raw': gpu.temperature, # เพิ่มค่าอุณหภูมิแบบดิบ
                'processes': gpu_processes.get(gpu.id, [])
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
