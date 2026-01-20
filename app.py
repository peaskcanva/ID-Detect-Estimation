import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PEA AI Auditor PRO", layout="wide")

# ส่วนหัวของแอป
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PEA AI PDF Auditor (Professional Edition)")
st.info("ระบบตรวจสภาพพัสดุและเปรียบเทียบมาตรฐาน พร้อมระบบตรวจจับรายการส่วนเกิน")

# --- ฐานข้อมูลมาตรฐาน (คืนค่าครบถ้วน) ---
TR_STANDARDS = {
    "50": {"TR_CODE": "1050010066", "items": {"1040020000": -3.0, "1040020010": 3.0, "1050010066": 1.0, "40205": 1.0, "14144": 1.0}},
    "100": {"TR_CODE": "1050010067", "items": {"1040020002": -6.0, "1040020012": 6.0, "1050010067": 1.0, "40205": 1.0, "14144": 1.0}},
    "160": {"TR_CODE": "1050010068", "items": {"1040020002": -3.0, "1040020012": 3.0, "1040020004": -3.0, "1040020014": 3.0, "1050010068": 1.0, "40205": 1.0}},
    "250": {"TR_CODE": "1050010069", "items": {"1040020004": -3.0, "1040020014": 3.0, "1040020005": -3.0, "1040020015": 3.0, "1050010069": 1.0, "40205": 1.0}}
}

# ฟังก์ชันสำหรับจัดรูปแบบสีในตาราง
def color_status(val):
    if val == "✅ ถูกต้อง": color = '#d4edda' # เขียวอ่อน
    elif val == "⚠️ จำนวนไม่ตรง": color = '#fff3cd' # เหลืองอ่อน
    else: color = '#f8d7da' # แดงอ่อน
    return f'background-color: {color}'

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ PDF (50/100/160/250 kVA)", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        clean_text = re.sub(r'\s+', '', full_text)

        # 1. ตรวจหาขนาดหม้อแปลง
        detected_size = next((sz for sz, d in TR_STANDARDS.items() if d["TR_CODE"] in clean_text), None)

        if detected_size:
            st.success(f"📌 ตรวจพบหม้อแปลงขนาด **{detected_size} kVA**")
            
            std_items = TR_STANDARDS[detected_size]["items"]
            audit_data = []
            found_codes_in_pdf = []

            # 2. ตรวจสอบตามรายการมาตรฐาน
            for code, std_qty in std_items.items():
                found_qty = 0.0
                status = "❌ ไม่พบในไฟล์"
                
                if code in clean_text:
                    found_codes_in_pdf.append(code)
                    match = re.search(f"{code}.*?(\n|$)", full_text)
                    if match:
                        nums = re.findall(r"-?\d+\.\d+", match.group(0))
                        if nums:
                            found_qty = float(nums[-1])
                            status = "✅ ถูกต้อง" if found_qty == std_qty else "⚠️ จำนวนไม่ตรง"
                
                audit_data.append({"รหัสพัสดุ": code, "จำนวนมาตรฐาน": std_qty, "จำนวนใน PDF": found_qty, "สถานะ": status})

            # 3. ตรวจสอบรายการ "เกิน" (มีใน PDF แต่ไม่มีในมาตรฐาน)
            extra_data = []
            # ค้นหารหัสพัสดุทั้งหมดใน PDF (สมมติว่ารหัสพัสดุคือตัวเลข 5-10 หลัก)
            all_codes_in_pdf = set(re.findall(r'\b\d{5,10}\b', clean_text))
            for code in all_codes_in_pdf:
                if code not in std_items and code != TR_STANDARDS[detected_size]["TR_CODE"]:
                    match = re.search(f"{code}.*?(\n|$)", full_text)
                    qty = "N/A"
                    if match:
                        nums = re.findall(r"-?\d+\.\d+", match.group(0))
                        if nums: qty = float(nums[-1])
                    extra_data.append({"รหัสพัสดุ": code, "จำนวนที่พบ": qty, "สถานะ": "🚩 รายการส่วนเกิน"})

            # --- แสดงผลตารางหลัก ---
            df_main = pd.DataFrame(audit_data)
            st.subheader("📊 ตารางตรวจสอบรายการมาตรฐาน")
            st.dataframe(df_main.style.applymap(color_status, subset=['สถานะ']), use_container_width=True)

            # --- แสดงผลรายการเกิน ---
            if extra_data:
                st.subheader("🚩 พบรายการที่อยู่นอกเหนือมาตรฐาน (Surplus)")
                df_extra = pd.DataFrame(extra_data)
                st.dataframe(df_extra, use_container_width=True)

            # --- ปุ่ม Download Excel ---
            st.divider()
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_main.to_excel(writer, index=False, sheet_name='Audit_Result')
                if extra_data:
                    pd.DataFrame(extra_data).to_excel(writer, index=False, sheet_name='Extra_Items')
            
            st.download_button(
                label="📥 Download ผลการตรวจสอบเป็น Excel",
                data=output.getvalue(),
                file_name=f"Audit_Result_{detected_size}kVA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        else:
            st.error("❌ ไม่พบรหัสหม้อแปลงที่รองรับในไฟล์นี้")
