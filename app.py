import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PEA ตรวจสอบ ประมาณการ", layout="wide")

# ปรับแต่ง CSS
st.markdown("""
    <style>
    .stDataFrame { border-radius: 10px; }
    .stButton>button { background-color: #007bff; color: white; font-weight: bold; }
    .match-tag { background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PEA ตรวจสอบข้อมูลและเปรียบเทียบรูปแบบการติดตั้ง")

# --- ฐานข้อมูลมาตรฐาน (ข้อมูลเดิมครบชุด + โครงสร้าง xxxx สำหรับรูปแบบที่ 2) ---
TR_STANDARDS = {
    "50": [
        {
            "variant": "50 kVA (2 Feeder - หม้อแปลงระบบจำหน่าย)",
            "TR_CODE": "1050010066",
            "items": {
                "1040020000": {"name": "L.T. H.R.C. FUSE 32-36 A.", "qty": -3.0},
                "1040020001": {"name": "L.T. H.R.C. FUSE 50 A.", "qty": -3.0},
                "1040020010": {"name": "H.R.C. FUSE, BLADE CONTACT, 32 A.", "qty": 3.0},
                "1040020011": {"name": "H.R.C. FUSE, BLADE CONTACT, 50 A.", "qty": 3.0},
                "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
                "1040020102": {"name": "FSD, FULL INSULATED, 1X400A, 400V", "qty": 6.0},
                "1050010066": {"name": "TR. 50 kVA, 3P", "qty": 1.0},
                "14019": {"name": "L.T. FUSE, 20KVA 3-P,4WIRE, 32A", "qty": 1.0},
                "14020": {"name": "L.T. FUSE, 30KVA 3-P,4WIRE, 50A", "qty": 1.0},
                "14144": {"name": "X-ARM-C WITH 6 L.T., 3-P, 2CCT ,12 M", "qty": 1.0},
                "40114": {"name": "LT WIRING 95 SQ.MM. TO L.T.", "qty": 2.0},
                "40205": {"name": "TR. INST. ON SINGLE POLE 50-250 kVA", "qty": 1.0}
            }
        },
        {
            "variant": "50 kVA (1 Feeder - หม้อแปลงเฉพาะราย)",
            "TR_CODE": "1050010066",
            "items": {
                "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -3.0},
                "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 3.0},
                "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -3.0},
                "1040020102": {"name": "FSD, FULL INSULATED, 1X400A, 400V", "qty": 3.0},
                "1050010066": {"name": "TR. 50 kVA, 3P", "qty": 1.0},
                "14021": {"name": "L.T. FUSE, 50KVA 3-P,4WIRE, 80A", "qty": 1.0},
                "14147": {"name": "X-ARM-C WITH 3 L.T., 3-P, 1CCT ,12.2, 14 M", "qty": 1.0},
                "40126": {"name": "LT WIRING 50 SQ.MM. TO METER", "qty": 1.0},
                "40205": {"name": "TR. INST. ON SINGLE POLE 50-250 kVA", "qty": 1.0}
            }
        }
    ],
    "100": [
        {
            "variant": "100 kVA (มาตรฐานเดิม)",
            "TR_CODE": "1050010067",
            "items": {
                "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -6.0},
                "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 6.0},
                "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
                "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
                "1050010067": {"name": "TR. 100 kVA, 3P", "qty": 1.0},
                "14021": {"name": "L.T. FUSE, 50KVA 3-P,4WIRE, 80A", "qty": 2.0},
                "14144": {"name": "X-ARM-C WITH 6 L.T., 3-P, 2CCT ,12 M", "qty": 1.0},
                "40114": {"name": "LT WIRING 95 SQ.MM. TO L.T.", "qty": 2.0},
                "40205": {"name": "TR. INST. ON SINGLE POLE 50-250 kVA", "qty": 1.0}
            }
        },
        {
            "variant": "100 kVA (รูปแบบที่ 2 - แก้ไขข้อมูลเอง)",
            "TR_CODE": "1050010067",
            "items": {
                "xxxx1": {"name": "รายการใหม่", "qty": 0.0}
            }
        }
    ],
    "160": [
        {
            "variant": "160 kVA (มาตรฐานเดิม)",
            "TR_CODE": "1050010068",
            "items": {
                "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -3.0},
                "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
                "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 3.0},
                "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},            
                "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
                "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
                "1050010068": {"name": "TR. 160 kVA, 3P", "qty": 1.0},
                "14021": {"name": "L.T. FUSE, 50KVA 3-P,4WIRE, 80A", "qty": 1.0},
                "14023": {"name": "L.T. FUSE, 100KVA 3-P,4WIRE, 160A", "qty": 1.0},
                "14144": {"name": "X-ARM-C WITH 6 L.T., 3-P, 2CCT ,12 M", "qty": 1.0},
                "40114": {"name": "LT WIRING 95 SQ.MM. TO L.T.", "qty": 2.0},
                "40205": {"name": "TR. INST. ON SINGLE POLE 50-250 kVA", "qty": 1.0}
            }
        },
        {
            "variant": "160 kVA (รูปแบบที่ 2 - แก้ไขข้อมูลเอง)",
            "TR_CODE": "1050010068",
            "items": {
                "xxxx1": {"name": "รายการใหม่", "qty": 0.0}
            }
        }
    ],
    "250": [
        {
            "variant": "250 kVA (มาตรฐานเดิม)",
            "TR_CODE": "1050010069",
            "items": {
                "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
                "1040020005": {"name": "L.T. H.R.C. FUSE 200 A.", "qty": -3.0},
                "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},
                "1040020015": {"name": "H.R.C. FUSE, BLADE CONTACT, 200 A.", "qty": 3.0},
                "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
                "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
                "1050010069": {"name": "TR. 250 kVA, 3P", "qty": 1.0},
                "14023": {"name": "L.T. FUSE, 100KVA 3-P,4WIRE, 160A", "qty": 1.0},
                "14024": {"name": "L.T. FUSE, 140KVA 3-P,4WIRE, 200A", "qty": 1.0},
                "14144": {"name": "X-ARM-C WITH 6 L.T., 3-P, 2CCT ,12 M", "qty": 1.0},
                "40115": {"name": "LT WIRING 120 SQ.MM. TO L.T.", "qty": 2.0},
                "40205": {"name": "TR. INST. ON SINGLE POLE 50-250 kVA", "qty": 1.0}
            }
        },
        {
            "variant": "250 kVA (รูปแบบที่ 2 - แก้ไขข้อมูลเอง)",
            "TR_CODE": "1050010069",
            "items": {
                "xxxx1": {"name": "รายการใหม่", "qty": 0.0}
            }
        }
    ]
}

def color_status(val):
    if val == "✅ ถูกต้อง": return 'background-color: #d4edda'
    if val == "⚠️ จำนวนไม่ตรง": return 'background-color: #fff3cd'
    return 'background-color: #f8d7da'

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ PDF ประมาณการ", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        clean_text_check = re.sub(r'\s+', '', full_text)
        
        # ตรวจหาขนาดหม้อแปลง
        size_detected = None
        for size, variants in TR_STANDARDS.items():
            if variants[0]["TR_CODE"] in clean_text_check:
                size_detected = size
                break

        if size_detected:
            st.success(f"📌 ตรวจพบหม้อแปลงขนาด **{size_detected} kVA**")
            
            all_variants = TR_STANDARDS[size_detected]
            scores = [] 

            # แบ่งหน้าจอแสดงผลตามจำนวน Variant
            cols = st.columns(len(all_variants))
            
            for idx, var in enumerate(all_variants):
                with cols[idx]:
                    st.subheader(f"📋 {var['variant']}")
                    check_list = var["items"]
                    audit_data = []
                    correct_items = 0

                    for code, std in check_list.items():
                        found_qty, status = 0.0, "❌ ไม่พบในไฟล์"
                        if code in clean_text_check:
                            row = re.search(f"{code}.*?(\n|$)", full_text)
                            if row:
                                nums = re.findall(r"-?\d+\.\d+", row.group(0))
                                if nums:
                                    found_qty = float(nums[-1])
                                    if found_qty == std['qty']:
                                        status = "✅ ถูกต้อง"
                                        correct_items += 1
                                    else:
                                        status = "⚠️ จำนวนไม่ตรง"
                        
                        audit_data.append({
                            "รหัสพัสดุ": code,
                            "รายการ": std['name'],
                            "มาตรฐาน": std['qty'],
                            "ในไฟล์": found_qty,
                            "สถานะ": status
                        })

                    st.dataframe(pd.DataFrame(audit_data).style.applymap(color_status, subset=['สถานะ']), use_container_width=True)
                    scores.append({"variant": var['variant'], "score": correct_items})

            # --- ส่วนสรุปผลการเปรียบเทียบ ---
            st.divider()
            best_variant = max(scores, key=lambda x: x['score'])
            st.markdown(f"### 💡 ผลการวิเคราะห์: ไฟล์นี้มีความใกล้เคียงกับ <span class='match-tag'>{best_variant['variant']}</span> มากที่สุด", unsafe_allow_html=True)
            st.write(f"(พบรายการที่ถูกต้องทั้งหมด {best_variant['score']} รายการ)")

        else:
            st.error("❌ ไม่พบรหัสหม้อแปลงที่กำหนดในฐานข้อมูลมาตรฐาน")
