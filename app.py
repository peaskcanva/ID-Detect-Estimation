import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PEA AI Auditor PRO", layout="wide")

# ปรับแต่ง CSS ให้ตารางดูสวยขึ้น
st.markdown("""
    <style>
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    .stButton>button { width: 100%; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PEA AI PDF Auditor (Full Standards Edition)")

# --- ฐานข้อมูลมาตรฐาน (รายการพัสดุชุดเดิมของคุณทั้งหมด) ---
TR_STANDARDS = {
    "50": {
        "TR_CODE": "1050010066",
        "items": {
            "1040020000": {"name": "L.T. H.R.C. FUSE 32-36 A.", "qty": -3.0},
            "1040020001": {"name": "L.T. H.R.C. FUSE 50 A.", "qty": -3.0},
            "1040020010": {"name": "H.R.C. FUSE, BLADE CONTACT, 32 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A, 400V", "qty": 6.0},
            "1050010066": {"name": "TR. 50 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "100": {
        "TR_CODE": "1050010067",
        "items": {
            "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -6.0},
            "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 6.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010067": {"name": "TR. 100 kVA, 3P", "qty": 1.0},
            "14021": {"name": "LT. FUSE SET (50 kVA)", "qty": 2.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "160": {
        "TR_CODE": "1050010068",
        "items": {
            "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -3.0},
            "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 3.0},
            "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
            "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010068": {"name": "TR. 160 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "250": {
        "TR_CODE": "1050010069",
        "items": {
            "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
            "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},
            "1040020005": {"name": "L.T. H.R.C. FUSE 200 A.", "qty": -3.0},
            "1040020015": {"name": "H.R.C. FUSE, BLADE CONTACT, 200 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010069": {"name": "TR. 250 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40115": {"name": "LT WIRING 120 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    }
}

# ฟังก์ชันใส่สีสถานะ
def color_status(val):
    if val == "✅ ถูกต้อง": color = '#d4edda'
    elif val == "⚠️ จำนวนไม่ตรง": color = '#fff3cd'
    else: color = '#f8d7da'
    return f'background-color: {color}'

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ PDF (50/100/160/250 kVA)", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"

        clean_text_check = re.sub(r'\s+', '', full_text)
        detected_size = next((sz for sz, data in TR_STANDARDS.items() if data["TR_CODE"] in clean_text_check), None)

        if detected_size:
            st.success(f"📌 ตรวจพบหม้อแปลงขนาด **{detected_size} kVA**")
            
            check_list = TR_STANDARDS[detected_size]["items"]
            audit_data = []

            # 1. ตรวจสอบรายการมาตรฐาน
            for code, std in check_list.items():
                found_qty = "ไม่พบ"
                status = "❌ ไม่พบในไฟล์"
                
                if code in clean_text_check:
                    row_match = re.search(f"{code}.*?(\n|$)", full_text)
                    if row_match:
                        all_numbers = re.findall(r"-?\d+\.\d+", row_match.group(0))
                        if all_numbers:
                            found_qty = float(all_numbers[-1])
                            status = "✅ ถูกต้อง" if found_qty == std['qty'] else "⚠️ จำนวนไม่ตรง"

                audit_data.append({
                    "รหัสพัสดุ": code,
                    "รายการ": std['name'],
                    "มาตรฐาน (Qty)": std['qty'],
                    "พบในไฟล์ (Qty)": found_qty,
                    "สถานะ": status
                })

            # 2. ตรวจสอบรายการส่วนเกิน (Surplus)
            extra_items = []
            # ค้นหารหัสพัสดุ 10 หลักในไฟล์
            all_found_codes = set(re.findall(r'\d{10}', clean_text_check))
            for f_code in all_found_codes:
                if f_code not in check_list and f_code != TR_STANDARDS[detected_size]["TR_CODE"]:
                    extra_items.append({"รหัสพัสดุ": f_code, "สถานะ": "🚩 รายการส่วนเกิน"})

            # แสดงตารางหลัก
            df_main = pd.DataFrame(audit_data)
            st.subheader("📊 ตารางเปรียบเทียบรายการมาตรฐาน")
            st.dataframe(df_main.style.applymap(color_status, subset=['สถานะ']), use_container_width=True)

            # แสดงตารางส่วนเกิน
            if extra_items:
                st.subheader("🚩 รายการที่พบในไฟล์แต่ไม่อยู่ในมาตรฐาน")
                st.dataframe(pd.DataFrame(extra_items), use_container_width=True)

            # ปุ่ม Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_main.to_excel(writer, index=False, sheet_name='Audit_Result')
                if extra_items:
                    pd.DataFrame(extra_items).to_excel(writer, index=False, sheet_name='Extra_Items')
            
            st.download_button(
                label="📥 Download ผลการตรวจสอบ (Excel)",
                data=output.getvalue(),
                file_name=f"Audit_{detected_size}kVA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ ไม่พบรหัสพัสดุหม้อแปลงที่กำหนดในไฟล์นี้")

    with st.expander("📝 ดูข้อความดิบจาก PDF"):
        st.text(full_text)
