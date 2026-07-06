---
description: Turn in place ~180° to reverse heading (CMD_VEL 0.0 m/s, +0.6 rad/s)
allowed-tools: Bash(ssh navbot-pi:*)
---

Rotate the navbot **in place ~180°** (spin left/CCW at 0.6 rad/s for ~5.2 s) to face the reverse direction, closed-loop. The angle is open-loop / time-based, so treat ~180° as approximate.

SAFETY — do this first, every time:
1. Confirm the Pi is reachable (`ssh navbot-pi 'echo ok'`); if not, tell the user and stop.
2. **This ROTATES the robot in place.** Ask the user to confirm clear space around the robot (it sweeps its own footprint) OR the wheels are on blocks. WAIT for explicit "yes" before driving.

Then run (background reader thread checksum-validates serial; main streams `CMD_VEL` at 10 Hz, then STOP):

```bash
ssh navbot-pi 'bash -s' <<'EOF'
python3 - <<'PY'
import serial, time, threading
PORT='/dev/serial/by-id/usb-Raspberry_Pi_Pico_E661410403114B35-if00'
LIN, ANG, SECS = 0.0, 0.6, 5.2   # in-place CCW; ~pi rad at 0.6 rad/s
s=serial.Serial(PORT,115200,timeout=0.1)
def xorcsum(b):
    c=0
    for ch in b.encode('utf-8','replace'): c^=ch
    return c
odom={'L':None,'R':None}; states=set(); lock=threading.Lock(); run=True
def reader():
    while run:
        try: raw=s.readline().decode('utf-8','replace').strip()
        except Exception: continue
        if not raw or '*' not in raw: continue
        body,_,cs=raw.rpartition('*')
        try:
            if len(cs)<2 or xorcsum(body)!=int(cs[:2],16): continue
        except ValueError: continue
        p=body.split()
        if body.startswith('ODOM') and len(p)>=4:
            with lock: odom['L'],odom['R']=int(p[2]),int(p[3])
        elif body.startswith('STATE') and len(p)>=3:
            with lock: states.add(' '.join(p[1:3]))
s.write(b'RESET\n'); time.sleep(0.4); s.reset_input_buffer()
th=threading.Thread(target=reader,daemon=True); th.start(); time.sleep(0.3)
with lock: bL,bR=odom['L'] or 0, odom['R'] or 0; states.clear()  # report only driving-phase states
t0=time.time(); ls=0
while time.time()-t0<SECS:
    if time.time()-ls>=0.1:
        s.write(f'CMD_VEL {LIN} {ANG}\n'.encode()); ls=time.time()
    time.sleep(0.02)
s.write(b'STOP\n'); s.write(b'CMD_VEL 0.0 0.0\n'); time.sleep(0.5)
run=False; th.join(timeout=1)
with lock:
    eL=odom['L'] if odom['L'] is not None else bL
    eR=odom['R'] if odom['R'] is not None else bR
    st=sorted(states)
dL,dR=eL-bL,eR-bR
print(f"LEFT delta={dL:+}  RIGHT delta={dR:+}")
print("states:", st)
print("RESULT:", "IN-PLACE CCW OK (left back, right fwd)" if dL<0 and dR>0 and 'FAULT STALL' not in st else "review")
s.close()
PY
EOF
```

Interpret: PASS = in-place rotation pattern — **left wheel counts down, right wheel counts up** (CCW), roughly equal magnitude, no `FAULT STALL`. If 180° lands short/long, adjust `SECS` (rotation rate varies with battery/load).
