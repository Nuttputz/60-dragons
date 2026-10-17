import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import calendar
from datetime import datetime

# ==========================================
# ระบบฐานข้อมูล Google Sheets
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
WORKSHEET_NAME = "Sheet1" # ต้องตรงกับชื่อชีตด้านล่างของ Google Sheets

def get_all_customers():
    try:
        df = conn.read(worksheet=WORKSHEET_NAME, ttl=0)
        df = df.dropna(subset=['id', 'name'])
        if not df.empty:
            df['id'] = pd.to_numeric(df['id'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["id", "name", "building_name", "birth_year", "gender", "kua_number", "degree", "dragon_name", "status", "record_date", "b_day", "b_month", "bazi_strength"])

def add_customer(name, building_name, birth_year, gender, kua, degree, dragon, status, b_day, b_month, bazi_strength):
    df = get_all_customers()
    next_id = 1 if df.empty else int(df['id'].max()) + 1
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    new_data = pd.DataFrame([{
        "id": next_id, "name": name, "building_name": building_name, 
        "birth_year": birth_year, "gender": gender, "kua_number": kua, 
        "degree": degree, "dragon_name": dragon, "status": status, 
        "record_date": date_str, "b_day": b_day, "b_month": b_month, "bazi_strength": bazi_strength
    }])
    
    updated_df = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet=WORKSHEET_NAME, data=updated_df)

def update_customer(cust_id, name, building_name, birth_year, gender, kua, degree, dragon, status, b_day, b_month, bazi_strength):
    df = get_all_customers()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    idx = df[df['id'] == cust_id].index
    if not idx.empty:
        df.loc[idx, ['name', 'building_name', 'birth_year', 'gender', 'kua_number', 'degree', 'dragon_name', 'status', 'record_date', 'b_day', 'b_month', 'bazi_strength']] = [name, building_name, birth_year, gender, kua, degree, dragon, status, date_str, b_day, b_month, bazi_strength]
        conn.update(worksheet=WORKSHEET_NAME, data=df)

def delete_customer(cust_id):
    df = get_all_customers()
    idx = df[df['id'] == cust_id].index
    if not idx.empty:
        df = df.drop(idx)
        conn.update(worksheet=WORKSHEET_NAME, data=df)

# ==========================================
# ฟังก์ชันคำนวณดวงจีน (Day Master) 
# ==========================================
def calculate_day_master(day, month, year_ce):
    try:
        anchor_date = datetime(2024, 1, 1)
        target_date = datetime(year_ce, month, day)
        delta_days = (target_date - anchor_date).days
        
        stem_num = (1 + delta_days) % 10
        if stem_num <= 0: stem_num += 10
            
        stems_data = {
            1: ("ไม้ (หยาง) / Jia", "ไม้"), 2: ("ไม้ (หยิน) / Yi", "ไม้"),
            3: ("ไฟ (หยาง) / Bing", "ไฟ"), 4: ("ไฟ (หยิน) / Ding", "ไฟ"),
            5: ("ดิน (หยาง) / Wu", "ดิน"), 6: ("ดิน (หยิน) / Ji", "ดิน"),
            7: ("ทอง (หยาง) / Geng", "ทอง"), 8: ("ทอง (หยิน) / Xin", "ทอง"),
            9: ("น้ำ (หยาง) / Ren", "น้ำ"), 10: ("น้ำ (หยิน) / Gui", "น้ำ")
        }
        return stems_data[stem_num]
    except Exception as e:
        return ("ไม่ทราบ", "ไม่ทราบ")

def get_bazi_relations(day_element, strength):
    cycles = {
        "ไม้": {"resource": "น้ำ", "companion": "ไม้", "output": "ไฟ", "wealth": "ดิน", "power": "ทอง"},
        "ไฟ": {"resource": "ไม้", "companion": "ไฟ", "output": "ดิน", "wealth": "ทอง", "power": "น้ำ"},
        "ดิน": {"resource": "ไฟ", "companion": "ดิน", "output": "ทอง", "wealth": "น้ำ", "power": "ไม้"},
        "ทอง": {"resource": "ดิน", "companion": "ทอง", "output": "น้ำ", "wealth": "ไม้", "power": "ไฟ"},
        "น้ำ": {"resource": "ทอง", "companion": "น้ำ", "output": "ไม้", "wealth": "ไฟ", "power": "ดิน"}
    }
    
    if day_element not in cycles: return [], [], ""
    c = cycles[day_element]
    
    if strength == "ดิถีอ่อน (WEAK)":
        fav = [c["resource"], c["companion"]]
        unfav = [c["power"], c["wealth"], c["output"]]
    else: 
        fav = [c["output"], c["wealth"], c["power"]]
        unfav = [c["resource"], c["companion"]]
        
    color_map = {
        "ไม้": "เขียว, ต้นไม้", "ไฟ": "แดง, ชมพู, ส้ม, ม่วง", 
        "ดิน": "เหลือง, น้ำตาล, โทนเอิร์ธ", "ทอง": "ขาว, เงิน, ทอง", 
        "น้ำ": "ฟ้า, น้ำเงิน, ดำ"
    }
    fav_colors = " และ ".join([color_map[e] for e in fav])
    return fav, unfav, fav_colors

# ==========================================
# ฟังก์ชันคำนวณรหัสบุคคล (Kua Number)
# ==========================================
def calculate_kua_exact(birth_year_ce, gender):
    year_str = str(birth_year_ce)
    digit_sum = sum(int(char) for char in year_str)
    while digit_sum > 9:
        digit_sum = sum(int(char) for char in str(digit_sum))
        
    if gender == 'male':
        if birth_year_ce >= 2000:
            kua = 11 - (digit_sum + 9) % 9 
            if kua <= 0: kua += 9
        else:
            kua = 11 - digit_sum
            while kua <= 0: kua += 9
        
        if kua == 5: kua, group = 2, "ราศีตะวันตก"
        elif kua in [1, 3, 4, 9]: group = "ราศีตะวันออก"
        else: group = "ราศีตะวันตก"
    else:
        if birth_year_ce >= 2000:
            kua = (digit_sum + 6) % 9
            if kua == 0: kua = 9
        else:
            kua = digit_sum + 4
            while kua > 9: kua = sum(int(char) for char in str(kua))
                
        if kua == 5: kua, group = 8, "ราศีตะวันตก"
        elif kua in [1, 3, 4, 9]: group = "ราศีตะวันออก"
        else: group = "ราศีตะวันตก"
            
    return {"kua_number": kua, "group": group}

# ==========================================
# ฐานข้อมูลผัง 8 ทิศ (โป๊ยข่วย)
# ==========================================
kua_bagua = {
    1: {"N": "ประธาน", "S": "อายุยืน", "E": "หมอเทพ", "SE": "รุ่งเรือง", "W": "ผีสิง", "NW": "โทษภัย", "SW": "สูญสิ้น", "NE": "ห้าผี"},
    2: {"SW": "ประธาน", "NW": "หมอเทพ", "W": "อายุยืน", "NE": "รุ่งเรือง", "S": "โทษภัย", "N": "สูญสิ้น", "E": "ผีสิง", "SE": "ห้าผี"},
    3: {"E": "ประธาน", "SE": "อายุยืน", "S": "รุ่งเรือง", "N": "หมอเทพ", "W": "สูญสิ้น", "NW": "ห้าผี", "SW": "ผีสิง", "NE": "โทษภัย"},
    4: {"SE": "ประธาน", "E": "อายุยืน", "S": "หมอเทพ", "N": "รุ่งเรือง", "W": "โทษภัย", "NW": "ผีสิง", "SW": "ห้าผี", "NE": "สูญสิ้น"},
    6: {"NW": "ประธาน", "SW": "อายุยืน", "W": "รุ่งเรือง", "NE": "หมอเทพ", "S": "สูญสิ้น", "N": "โทษภัย", "E": "ห้าผี", "SE": "ผีสิง"},
    7: {"W": "ประธาน", "NW": "รุ่งเรือง", "SW": "หมอเทพ", "NE": "อายุยืน", "S": "ห้าผี", "N": "ผีสิง", "E": "สูญสิ้น", "SE": "โทษภัย"},
    8: {"NE": "ประธาน", "NW": "หมอเทพ", "W": "อายุยืน", "SW": "รุ่งเรือง", "S": "ผีสิง", "N": "ห้าผี", "E": "โทษภัย", "SE": "สูญสิ้น"},
    9: {"S": "ประธาน", "N": "อายุยืน", "E": "รุ่งเรือง", "SE": "หมอเทพ", "W": "ห้าผี", "NW": "สูญสิ้น", "SW": "โทษภัย", "NE": "ผีสิง"}
}

def get_house_kua(degree):
    deg = degree % 360
    if (deg >= 337.6) or (deg <= 22.5): return {"facing": "เหนือ (N)", "sitting": "ใต้ (S)", "kua": 9, "name": "บ้านหลี่ (Li)", "group": "ราศีตะวันออก"}
    elif 22.6 <= deg <= 67.5: return {"facing": "ตะวันออกเฉียงเหนือ (NE)", "sitting": "ตะวันตกเฉียงใต้ (SW)", "kua": 2, "name": "บ้านคุน (Kun)", "group": "ราศีตะวันตก"}
    elif 67.6 <= deg <= 112.5: return {"facing": "ตะวันออก (E)", "sitting": "ตะวันตก (W)", "kua": 7, "name": "บ้านตุ้ย (Dui)", "group": "ราศีตะวันตก"}
    elif 112.6 <= deg <= 157.5: return {"facing": "ตะวันออกเฉียงใต้ (SE)", "sitting": "ตะวันตกเฉียงเหนือ (NW)", "kua": 6, "name": "บ้านเฉียน (Qian)", "group": "ราศีตะวันตก"}
    elif 157.6 <= deg <= 202.5: return {"facing": "ใต้ (S)", "sitting": "เหนือ (N)", "kua": 1, "name": "บ้านขั่น (Kan)", "group": "ราศีตะวันออก"}
    elif 202.6 <= deg <= 247.5: return {"facing": "ตะวันตกเฉียงใต้ (SW)", "sitting": "ตะวันออกเฉียงเหนือ (NE)", "kua": 8, "name": "บ้านเกิน (Gen)", "group": "ราศีตะวันตก"}
    elif 247.6 <= deg <= 292.5: return {"facing": "ตะวันตก (W)", "sitting": "ตะวันออก (E)", "kua": 3, "name": "บ้านเจิ้น (Zhen)", "group": "ราศีตะวันออก"}
    elif 292.6 <= deg <= 337.5: return {"facing": "ตะวันตกเฉียงเหนือ (NW)", "sitting": "ตะวันออกเฉียงใต้ (SE)", "kua": 4, "name": "บ้านซวิ่น (Xun)", "group": "ราศีตะวันออก"}
    return None

def render_bagua_octagon(kua_num):
    if kua_num not in kua_bagua: return
    bagua = kua_bagua[kua_num]
    colors = {"รุ่งเรือง": "#d4edda", "หมอเทพ": "#d4edda", "อายุยืน": "#d4edda", "ประธาน": "#d4edda", "สูญสิ้น": "#f8d7da", "ห้าผี": "#f8d7da", "โทษภัย": "#f8d7da", "ผีสิง": "#f8d7da"}
    text_colors = {"รุ่งเรือง": "#155724", "หมอเทพ": "#155724", "อายุยืน": "#155724", "ประธาน": "#155724", "สูญสิ้น": "#721c24", "ห้าผี": "#721c24", "โทษภัย": "#721c24", "ผีสิง": "#721c24"}
    directions = [("N", "เหนือ", 0, "337.6° - 22.5°"), ("NE", "ต.อ.เฉียงเหนือ", 45, "22.6° - 67.5°"), ("E", "ตะวันออก", 90, "67.6° - 112.5°"), ("SE", "ต.อ.เฉียงใต้", 135, "112.6° - 157.5°"), ("S", "ใต้", 180, "157.6° - 202.5°"), ("SW", "ต.ตกเฉียงใต้", 225, "202.6° - 247.5°"), ("W", "ตะวันตก", 270, "247.6° - 292.5°"), ("NW", "ต.ตกเฉียงเหนือ", 315, "292.6° - 337.5°")]

    svg = '<div style="display: flex; justify-content: center; margin: 20px 0;"><svg viewBox="0 0 400 400" width="100%" max-width="450px" height="450" xmlns="http://www.w3.org/2000/svg"><g transform="translate(200,200)">'
    R = 180 
    for dir_key, dir_th, angle, deg_text in directions:
        status = bagua[dir_key]
        bg = colors.get(status, "#eee"); txt = text_colors.get(status, "#333")
        a1 = math.radians(angle - 22.5); a2 = math.radians(angle + 22.5)
        x1 = R * math.sin(a1); y1 = -R * math.cos(a1); x2 = R * math.sin(a2); y2 = -R * math.cos(a2)
        svg += f'<path d="M 0 0 L {x1} {y1} L {x2} {y2} Z" fill="{bg}" stroke="#ffffff" stroke-width="4"/>'
        a_mid = math.radians(angle)
        tx = 115 * math.sin(a_mid); ty = -115 * math.cos(a_mid)
        svg += f'<text x="{tx}" y="{ty-15}" text-anchor="middle" fill="{txt}" font-weight="bold" font-size="14">{dir_th} ({dir_key})</text><text x="{tx}" y="{ty+5}" text-anchor="middle" fill="{txt}" font-weight="bold" font-size="18">{status}</text><text x="{tx}" y="{ty+25}" text-anchor="middle" fill="{txt}" font-size="11">{deg_text}</text>'
    svg += '<circle cx="0" cy="0" r="15" fill="#ffffff" stroke="#cccccc" stroke-width="3"/></g></svg></div>'
    st.markdown(svg, unsafe_allow_html=True)

def find_dragon(deg, dataframe):
    for index, row in dataframe.iterrows():
        start = row['Degree_Start']; end = row['Degree_End']
        if start < end:
            if start <= deg <= end: return row
        else:
            if deg >= start or deg <= end: return row
    return None

@st.cache_data
def load_dragon_data():
    return pd.read_csv("dragons_data.csv")

df = load_dragon_data()

# ==========================================
# หน้าจอ UI
# ==========================================
st.set_page_config(page_title="ฮวงจุ้ย 60 มังกร", layout="centered")
st.title("🧭 ระบบฮวงจุ้ย 60 มังกร & ฐานข้อมูลลูกค้า")

tab1, tab3, tab2, tab4 = st.tabs(["👤 วิเคราะห์ดวงบุคคล", "🏠 วิเคราะห์ดวงบ้าน", "🧭 ค้นหาองศามังกร (สร้างบ้าน)", "📂 ฐานข้อมูลลูกค้า (CRM)"])

# ----------------- TAB 1 (ดวงบุคคล) -----------------
with tab1:
    st.header("วิเคราะห์ความเข้ากันได้ของคนกับบ้าน")
    col_name1, col_name2 = st.columns(2)
    with col_name1: customer_name = st.text_input("ชื่อ-นามสกุล ลูกค้า", placeholder="เช่น คุณสมชาย รักดี")
    with col_name2: building_name = st.text_input("ชื่อสถานที่/อาคาร", placeholder="เช่น บ้านพัก, ออฟฟิศสาขา 1")
    
    st.write("**ข้อมูลวันเกิดเพื่อหาดิถีธาตุ (Day Master) ตามหลัก Bazi**")
    date_c1, date_c2, date_c3 = st.columns([1,1.5,1])
    months_th = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    
    with date_c1: b_day = st.number_input("วันที่", min_value=1, max_value=31, value=1)
    with date_c2: b_month_str = st.selectbox("เดือน", months_th)
    with date_c3: b_year_be = st.number_input("ปีเกิด (พ.ศ.)", min_value=2443, max_value=2569, value=2535)
    
    b_month = months_th.index(b_month_str) + 1
    birth_year_ce = b_year_be - 543 
    
    max_days = calendar.monthrange(birth_year_ce, b_month)[1]
    b_day = min(b_day, max_days)

    col1, col2, col3 = st.columns(3)
    with col1: gender = st.selectbox("เพศ", ["ชาย", "หญิง"])
    with col2: degree = st.number_input("องศาหน้าบ้าน/อาคาร", min_value=0.0, max_value=360.0, value=0.0, step=0.1)
    with col3: bazi_strength = st.selectbox("กำลังดิถี", ["ดิถีอ่อน (WEAK)", "ดิถีแข็ง (STRONG)"])

    gender_en = 'male' if gender == "ชาย" else 'female'
    user_profile = calculate_kua_exact(birth_year_ce, gender_en) 
    kua = user_profile['kua_number']
    
    bazi_stem_name, bazi_element = calculate_day_master(b_day, b_month, birth_year_ce)
    fav_elements, unfav_elements, fav_colors = get_bazi_relations(bazi_element, bazi_strength)
    house_info = get_house_kua(degree)

    if house_info:
        st.write("### 🏠 1. ผังดี-ร้าย 8 ทิศ ประจำบ้าน")
        st.markdown(f"""
        <div style='background-color:#e2e3e5; padding:10px; border-radius:5px; margin-bottom:10px;'>
            <b>{house_info['name']} (รหัสบ้าน {house_info['kua']})</b> | หน้าบ้าน: {house_info['facing']} | หลังบ้าน: {house_info['sitting']}
        </div>
        """, unsafe_allow_html=True)
        render_bagua_octagon(house_info['kua']) 

    st.divider()

    st.write("### 👤 2. วิเคราะห์ดวงบุคคล (Kua & Bazi)")
    st.markdown(f"""
    <div style='background-color:#d1ecf1; padding:10px; border-radius:5px; margin-bottom:15px; border-left: 5px solid #17a2b8;'>
        <b>รหัสบุคคล (Kua Number): {kua}</b> | {user_profile['group']}
    </div>
    <div style='background-color:#fcf8e3; padding:15px; border-radius:8px; margin-bottom:20px; border: 1px solid #faebcc;'>
        <h4 style='color:#8a6d3b; margin-top:0;'>☯️ วิเคราะห์ปาจื่อ (Bazi Day Master)</h4>
        <p style='color:#8a6d3b; font-size:1em; margin-bottom:10px;'>
            คำนวณจากเสาวันเกิด (Day Pillar): <b>{b_day} {b_month_str} พ.ศ.{b_year_be}</b>
        </p>
        <ul style='color:#8a6d3b; font-size:1.1em;'>
            <li><b>ธาตุดิถีประจำตัว (Day Master):</b> <b>{bazi_stem_name}</b></li>
            <li><b>สถานะดิถี:</b> {bazi_strength}</li>
            <li><b>✅ ธาตุให้คุณ (Favorable):</b> {", ".join(fav_elements) if fav_elements else "-"}</li>
            <li><b>❌ ธาตุให้โทษ (Unfavorable):</b> {", ".join(unfav_elements) if unfav_elements else "-"}</li>
            <li><b>🎨 สีมงคลเสริมดวง:</b> {fav_colors}</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    render_bagua_octagon(kua) 
    
    if house_info:
        st.write("### 🤝 3. สรุปความเข้ากันได้ (ดวงคน vs ดวงบ้าน)")
        east_group = [1, 3, 4, 9]
        if (kua in east_group) == (house_info['kua'] in east_group):
            match_status = "✨ ส่งเสริมกัน (เข้ากันได้ดีมาก)"
            match_color = "#d4edda" ; text_color = "#155724"
            match_desc = f"ดวงบุคคล ({user_profile['group']}) และดวงบ้าน ({house_info['group']}) อยู่ในกลุ่มราศีเดียวกัน พลังงานคอยเกื้อหนุนให้มีความเจริญรุ่งเรือง มั่นคง"
        else:
            match_status = "⚠️ ขัดแย้งกัน (ปะทะพลังงาน)"
            match_color = "#f8d7da" ; text_color = "#721c24"
            match_desc = f"ดวงบุคคล ({user_profile['group']}) และดวงบ้าน ({house_info['group']}) อยู่ต่างกลุ่มราศีกัน พลังงานของบ้านไม่ส่งเสริมโดยตรง ควรแก้เคล็ดด้วยการหันเตียงนอน"
            
        st.markdown(f"""
        <div style='background-color:{match_color}; color:{text_color}; padding:15px; border-radius:8px; border: 1px solid {text_color}; margin-bottom:20px;'>
            <h4 style='margin-top:0; color:{text_color};'>{match_status}</h4>
            <p style='margin-bottom:0;'>{match_desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    if st.button("🔍 บันทึกและวิเคราะห์มังกร", type="primary", use_container_width=True):
        if not customer_name or not building_name:
            st.warning("กรุณากรอกชื่อลูกค้า และชื่อสถานที่ก่อนทำการวิเคราะห์ครับ")
        else:
            dragon_result = find_dragon(degree, df)
            if dragon_result is not None:
                st.subheader(f"ผลวิเคราะห์มังกรที่องศา: {degree}°")
                status_color = "green" if "ดี" in str(dragon_result['Status']) else "red"
                dragon_element = dragon_result['Element']
                is_favorable = dragon_element in fav_elements
                is_unfavorable = dragon_element in unfav_elements
                
                if is_favorable:
                    element_match_msg = f"<br><span style='color:green;'>✨ <b>ธาตุมังกรให้คุณ:</b> มังกรธาตุ{dragon_element} เป็นธาตุที่ให้โชคและส่งเสริมดิถีธาตุ{bazi_element} ของลูกค้า!</span>"
                elif is_unfavorable:
                    element_match_msg = f"<br><span style='color:red;'>⚠️ <b>ธาตุมังกรให้โทษ:</b> มังกรธาตุ{dragon_element} ขัดแย้งกับดิถีธาตุ{bazi_element} ของลูกค้า ควรหลีกเลี่ยงหรือจัดฮวงจุ้ยแก้เคล็ด</span>"
                else:
                    element_match_msg = f"<br><span style='color:#555;'>👉 <b>ธาตุมังกรเป็นกลาง:</b> มังกรธาตุ{dragon_element} เข้ากันได้กับดิถีธาตุ{bazi_element} แบบเป็นกลาง</span>"

                st.markdown(f"### มังกรตัวที่ {dragon_result['ID']} ชื่อ **{dragon_result['Name']}** (ธาตุ{dragon_result['Element']})")
                st.markdown(f"สถานะมังกร: <span style='color:{status_color}; font-weight:bold; font-size: 1.2em;'>{dragon_result['Status']}</span> {element_match_msg}", unsafe_allow_html=True)
                st.info(f"**คำทำนาย:** {dragon_result['Description']}")
                
                add_customer(customer_name, building_name, birth_year_ce, gender, kua, degree, dragon_result['Name'], dragon_result['Status'], b_day, b_month, bazi_strength)
                st.success("💾 บันทึกข้อมูลสถานที่ลงฐานข้อมูลออนไลน์เรียบร้อยแล้ว!")
            else:
                st.error("ไม่พบข้อมูลมังกรในองศานี้")

# ----------------- TAB 3 (ดวงบ้านโดยเฉพาะ) -----------------
with tab3:
    st.header("วิเคราะห์รหัสบ้าน (House Kua)")
    st.write("กรอกองศาหน้าบ้าน เพื่อตรวจสอบรหัสประจำบ้าน ทิศมงคลของบ้าน และตำแหน่งมังกร")
    house_degree = st.number_input("กรอกองศาหน้าบ้าน (0.0 - 360.0)", min_value=0.0, max_value=360.0, value=0.0, step=0.1, key="house_deg")
    if st.button("🔍 วิเคราะห์รหัสบ้าน", type="primary", use_container_width=True):
        house_info = get_house_kua(house_degree)
        dragon_result = find_dragon(house_degree, df)
        if house_info:
            st.markdown(f"""
            <div style='background-color:#f8f9fa; border-left: 5px solid #0056b3; padding:15px; margin-bottom:20px;'>
                <h3 style='margin-top:0;'>🏡 {house_info['name']} (รหัส {house_info['kua']})</h3>
                <b>หน้าบ้านหันไปทิศ:</b> {house_info['facing']}<br>
                <b>หลังบ้านพิงทิศ:</b> {house_info['sitting']}<br>
                <b>จัดอยู่ในกลุ่ม:</b> {house_info['group']}
            </div>
            """, unsafe_allow_html=True)
            st.write("### 🗺️ ผังดี-ร้าย 8 ทิศ ประจำบ้าน")
            render_bagua_octagon(house_info['kua'])
            
            if dragon_result is not None:
                st.write(f"### 🐉 มังกรประจำองศานี้ ({house_degree}°)")
                status_color = "green" if "ดี" in str(dragon_result['Status']) else "red"
                st.markdown(f"**มังกรตัวที่ {dragon_result['ID']} ชื่อ {dragon_result['Name']}** (ธาตุ{dragon_result['Element']})")
                st.markdown(f"สถานะ: <span style='color:{status_color}; font-weight:bold;'>{dragon_result['Status']}</span>", unsafe_allow_html=True)
                st.info(f"**คำทำนาย:** {dragon_result['Description']}")

# ----------------- TAB 2 (ค้นหามังกร) -----------------
with tab2:
    st.header("ค้นหาองศามังกรสร้างบ้าน")
    
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1: element_filter = st.selectbox("เลือกธาตุมังกรที่ต้องการหา", ["ทั้งหมด", "ทอง", "น้ำ", "ไม้", "ไฟ", "ดิน"])
    with col_filter2: status_filter = st.radio("เลือกสถานะมังกร", ["เฉพาะมังกรที่ดี 🟢", "ทั้งหมด"])
        
    if st.button("🔍 ค้นหาองศามงคล", type="primary", use_container_width=True):
        filtered_df = df.copy()
        if element_filter != "ทั้งหมด": filtered_df = filtered_df[filtered_df['Element'] == element_filter]
        if status_filter == "เฉพาะมังกรที่ดี 🟢": filtered_df = filtered_df[filtered_df['Status'].str.contains("ดี", na=False)]
            
        if not filtered_df.empty:
            st.success(f"พบข้อมูลมังกรที่ตรงเงื่อนไขทั้งหมด {len(filtered_df)} ตัว")
            for idx, row in filtered_df.iterrows():
                is_good = "ดี" in str(row['Status'])
                bg_color = "#d4edda" if is_good else "#f8d7da"
                border_color = "#c3e6cb" if is_good else "#f5c6cb"
                text_color = "#155724" if is_good else "#721c24"
                
                st.markdown(f"""
                <div style='background-color:{bg_color}; border: 1px solid {border_color}; padding:15px; border-radius:8px; margin-bottom:15px;'>
                    <h4 style='margin-top:0; color:{text_color};'>🐉 มังกรตัวที่ {row['ID']}: {row['Name']} (ธาตุ{row['Element']})</h4>
                    <ul style='color:{text_color}; font-size:1.1em;'>
                        <li><b>องศาที่ครอบคลุม:</b> {row['Degree_Start']}° - {row['Degree_End']}°</li>
                        <li><b>สถานะ:</b> {row['Status']}</li>
                    </ul>
                    <p style='margin-bottom:0; color:{text_color}; font-size:0.95em;'><b>คำทำนาย:</b> {row['Description']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("ไม่พบมังกรที่ตรงกับเงื่อนไขที่คุณเลือก ลองปรับการค้นหาดูอีกครั้งครับ")

# ----------------- TAB 4 (CRM) -----------------
with tab4:
    st.header("📂 จัดการข้อมูลลูกค้า (Google Sheets)")
    
    df_customers = get_all_customers()
    
    if not df_customers.empty:
        df_display = df_customers.copy()
        df_display['birth_year'] = pd.to_numeric(df_display['birth_year'], errors='coerce').fillna(0).astype(int) + 543
        
        df_display = df_display.rename(columns={
            "id": "รหัส", "name": "ชื่อ-นามสกุล", "building_name": "สถานที่/อาคาร",
            "birth_year": "ปีเกิด (พ.ศ.)", "gender": "เพศ", "kua_number": "รหัส Kua",
            "degree": "องศา", "dragon_name": "ตำแหน่งมังกร",
            "status": "ผลลัพธ์", "record_date": "เวลาที่บันทึก"
        })
        
        display_cols = ["รหัส", "ชื่อ-นามสกุล", "สถานที่/อาคาร", "ปีเกิด (พ.ศ.)", "เพศ", "รหัส Kua", "องศา", "ตำแหน่งมังกร", "ผลลัพธ์", "เวลาที่บันทึก"]
        st.dataframe(df_display[display_cols], use_container_width=True, hide_index=True)
        st.divider()
        
        st.subheader("🔮 ดึงข้อมูลและแก้ไขข้อมูลลูกค้า")
        customer_options = df_customers['id'].astype(int).astype(str) + " - " + df_customers['name'] + " (" + df_customers['building_name'] + ")"
        selected_customer = st.selectbox("🔍 ค้นหาและเลือกข้อมูลลูกค้า:", customer_options)
        
        if selected_customer:
            selected_id = int(selected_customer.split(" - ")[0])
            cust_row = df_customers[df_customers['id'] == selected_id].iloc[0]
            cust_birth_be = int(cust_row['birth_year']) + 543 
            
            c_day = int(cust_row.get('b_day', 1))
            c_month = int(cust_row.get('b_month', 1))
            c_strength = cust_row.get('bazi_strength', 'ดิถีอ่อน (WEAK)')
            if pd.isna(c_day): c_day = 1
            if pd.isna(c_month): c_month = 1
            if pd.isna(c_strength): c_strength = 'ดิถีอ่อน (WEAK)'
            
            with st.expander("✏️ คลิกที่นี่เพื่อแก้ไขข้อมูลลูกค้า"):
                with st.form("edit_customer_form"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1: new_name = st.text_input("ชื่อ-นามสกุล", value=cust_row['name'])
                    with e_col2: new_building = st.text_input("ชื่อสถานที่/อาคาร", value=cust_row['building_name'])
                        
                    st.write("**ข้อมูลวันเกิด**")
                    dc1, dc2, dc3 = st.columns(3)
                    with dc1: new_day = st.number_input("วันที่", 1, 31, c_day)
                    with dc2: 
                        m_list = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
                        new_month_str = st.selectbox("เดือน", m_list, index=c_month-1)
                    with dc3: 
                        new_year_be = st.number_input("ปีเกิด (พ.ศ.)", min_value=2443, max_value=2569, value=cust_birth_be)
                        
                    e_col4, e_col5, e_col6 = st.columns(3)
                    with e_col4:
                        g_index = 0 if cust_row['gender'] == "ชาย" else 1
                        new_gender = st.selectbox("เพศ", ["ชาย", "หญิง"], index=g_index)
                    with e_col5:
                        s_idx = 0 if c_strength == "ดิถีอ่อน (WEAK)" else 1
                        new_strength = st.selectbox("กำลังดิถี", ["ดิถีอ่อน (WEAK)", "ดิถีแข็ง (STRONG)"], index=s_idx)
                    with e_col6:
                        new_deg = st.number_input("องศา", min_value=0.0, max_value=360.0, value=float(cust_row['degree']), step=0.1)
                        
                    if st.form_submit_button("💾 บันทึกการแก้ไข"):
                        new_year = new_year_be - 543 
                        new_m_idx = m_list.index(new_month_str) + 1
                        max_d = calendar.monthrange(new_year, new_m_idx)[1]
                        new_day = min(new_day, max_d)
                        
                        g_en = 'male' if new_gender == "ชาย" else 'female'
                        new_kua = calculate_kua_exact(new_year, g_en)['kua_number']
                        dragon_res = find_dragon(new_deg, df)
                        dr_name = dragon_res['Name'] if dragon_res is not None else "ไม่พบ"
                        dr_status = dragon_res['Status'] if dragon_res is not None else "ไม่พบ"
                        
                        update_customer(selected_id, new_name, new_building, new_year, new_gender, new_kua, new_deg, dr_name, dr_status, new_day, new_m_idx, new_strength)
                        st.success("อัปเดตข้อมูลสำเร็จ! ระบบกำลังดึงข้อมูลใหม่จากคลาวด์...")
                        st.rerun()

            st.markdown("---")
            
            st.markdown(f"""
            <div style='background-color:#f0f2f6; padding:15px; border-radius:10px; margin-bottom:15px;'>
                <b>👤 ชื่อ:</b> {cust_row['name']} &nbsp;|&nbsp; 
                <b>🏢 สถานที่:</b> {cust_row['building_name']} <br>
                <b>⚥ เพศ:</b> {cust_row['gender']} &nbsp;|&nbsp; 
                <b>📅 วันเกิด:</b> {c_day} {months_th[c_month-1]} พ.ศ.{cust_birth_be} &nbsp;|&nbsp; 
                <b>🧭 องศา:</b> {cust_row['degree']}°
            </div>
            """, unsafe_allow_html=True)
            
            house_info = get_house_kua(cust_row['degree'])
            if house_info:
                st.write("### 🏠 1. ผังดี-ร้าย 8 ทิศ ประจำบ้าน")
                st.markdown(f"""
                <div style='background-color:#e2e3e5; padding:10px; border-radius:5px; margin-bottom:10px;'>
                    <b>{house_info['name']} (รหัสบ้าน {house_info['kua']})</b> | หน้าบ้าน: {house_info['facing']} | หลังบ้าน: {house_info['sitting']}
                </div>
                """, unsafe_allow_html=True)
                render_bagua_octagon(house_info['kua'])
                
            st.divider()
            
            g_en_cust = 'male' if cust_row['gender'] == "ชาย" else 'female'
            u_prof_cust = calculate_kua_exact(int(cust_row['birth_year']), g_en_cust)
            bazi_stem_cust, bazi_ele_cust = calculate_day_master(c_day, c_month, int(cust_row['birth_year']))
            fav_cust, unfav_cust, fcol_cust = get_bazi_relations(bazi_ele_cust, c_strength)
            
            st.write("### 👤 2. วิเคราะห์ดวงบุคคล (Kua & Bazi)")
            st.markdown(f"""
            <div style='background-color:#d1ecf1; padding:10px; border-radius:5px; margin-bottom:15px; border-left: 5px solid #17a2b8;'>
                <b>รหัสบุคคล (Kua Number): {cust_row['kua_number']}</b> | {u_prof_cust['group']}
            </div>
            <div style='background-color:#fcf8e3; padding:15px; border-radius:8px; margin-bottom:20px; border: 1px solid #faebcc;'>
                <h4 style='color:#8a6d3b; margin-top:0;'>☯️ วิเคราะห์ปาจื่อ (Bazi Day Master)</h4>
                <ul style='color:#8a6d3b; font-size:1.1em;'>
                    <li><b>ธาตุดิถีประจำตัว (Day Master):</b> <b>{bazi_stem_cust}</b></li>
                    <li><b>สถานะดิถี:</b> {c_strength}</li>
                    <li><b>✅ ธาตุให้คุณ (Favorable):</b> {", ".join(fav_cust) if fav_cust else "-"}</li>
                    <li><b>❌ ธาตุให้โทษ (Unfavorable):</b> {", ".join(unfav_cust) if unfav_cust else "-"}</li>
                    <li><b>🎨 สีมงคลเสริมดวง:</b> {fcol_cust}</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            render_bagua_octagon(cust_row['kua_number'])
            
            if house_info:
                st.write("### 🤝 3. สรุปความเข้ากันได้ (ดวงคน vs ดวงบ้าน)")
                east_group = [1, 3, 4, 9]
                if (cust_row['kua_number'] in east_group) == (house_info['kua'] in east_group):
                    m_stat = "✨ ส่งเสริมกัน (เข้ากันได้ดีมาก)"
                    m_bg = "#d4edda" ; m_txt = "#155724"
                    m_desc = f"ดวงบุคคล ({u_prof_cust['group']}) และดวงบ้าน ({house_info['group']}) อยู่ในกลุ่มราศีเดียวกัน พลังงานคอยเกื้อหนุนให้มีความเจริญรุ่งเรือง มั่นคง"
                else:
                    m_stat = "⚠️ ขัดแย้งกัน (ปะทะพลังงาน)"
                    m_bg = "#f8d7da" ; m_txt = "#721c24"
                    m_desc = f"ดวงบุคคล ({u_prof_cust['group']}) และดวงบ้าน ({house_info['group']}) อยู่ต่างกลุ่มราศีกัน พลังงานของบ้านไม่ส่งเสริมโดยตรง ควรจัดเตียงหรือโต๊ะทำงานแก้เคล็ด"
                    
                st.markdown(f"""
                <div style='background-color:{m_bg}; color:{m_txt}; padding:15px; border-radius:8px; border: 1px solid {m_txt}; margin-bottom:20px;'>
                    <h4 style='margin-top:0; color:{m_txt};'>{m_stat}</h4>
                    <p style='margin-bottom:0;'>{m_desc}</p>
                </div>
                """, unsafe_allow_html=True)
                
            st.divider()
            dragon_result = find_dragon(cust_row['degree'], df)
            if dragon_result is not None:
                status_color = "green" if "ดี" in str(dragon_result['Status']) else "red"
                
                dragon_element_cust = dragon_result['Element']
                is_fav_crm = dragon_element_cust in fav_cust
                is_unfav_crm = dragon_element_cust in unfav_cust
                
                if is_fav_crm:
                    elem_msg_cust = f"<br><span style='color:green;'>✨ <b>ธาตุมังกรให้คุณ:</b> มังกรธาตุ{dragon_element_cust} ส่งเสริมดิถีธาตุ{bazi_ele_cust} ของลูกค้า!</span>"
                elif is_unfav_crm:
                    elem_msg_cust = f"<br><span style='color:red;'>⚠️ <b>ธาตุมังกรให้โทษ:</b> มังกรธาตุ{dragon_element_cust} บั่นทอนดิถีธาตุ{bazi_ele_cust} ของลูกค้า</span>"
                else:
                    elem_msg_cust = f"<br><span style='color:#555;'>👉 <b>ธาตุมังกรเป็นกลาง:</b> มังกรธาตุ{dragon_element_cust} เข้ากันได้แบบเป็นกลางกับดิถีธาตุ{bazi_ele_cust}</span>"

                st.write(f"### 🐉 4. คำทำนาย 60 มังกร (องศา {cust_row['degree']}°)")
                st.markdown(f"**มังกรตัวที่ {dragon_result['ID']} ชื่อ {dragon_result['Name']}** (ธาตุ{dragon_result['Element']})")
                st.markdown(f"สถานะ: <span style='color:{status_color}; font-weight:bold;'>{dragon_result['Status']}</span> {elem_msg_cust}", unsafe_allow_html=True)
                st.info(f"**คำทำนาย:** {dragon_result['Description']}")

        st.divider()
        
        st.subheader("🗑️ ลบข้อมูล")
        col_del1, col_del2 = st.columns([3, 1])
        with col_del1: delete_opt = st.selectbox("เลือก ID ที่ต้องการลบ", customer_options, key="del_box")
        with col_del2:
            st.write("")
            st.write("")
            if st.button("ลบข้อมูล", type="secondary"):
                del_id = int(delete_opt.split(" - ")[0])
                delete_customer(del_id)
                st.success(f"ลบข้อมูลสำเร็จ! ระบบกำลังดึงข้อมูลใหม่...")
                st.rerun() 
    else:
        st.info("ยังไม่มีข้อมูลลูกค้าในระบบครับ")