import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# โหลดค่า Environment Variables
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("กรุณาตั้งค่า GEMINI_API_KEY ในไฟล์ .env ก่อนเริ่มต้นใช้งานระบบ")

# เริ่มต้นเปิดใช้งาน GenAI Client
client = genai.Client()

# 1. กำหนด Mock Tool สำหรับระบบ Function Calling
def check_shipping_regulations(item_type: str, freight_method: str) -> dict:
    """Check dangerous goods international shipping regulations and restrictions."""
    if "air" in freight_method.lower() and ("flammable" in item_type.lower() or "spray" in item_type.lower()):
        return {"status": "RESTRICTED", "reason": "Flammable aerosols are strictly prohibited on air freight via IATA regulations."}
    return {"status": "APPROVED", "reason": "No major restrictions found for this cargo type on the selected freight method."}

# 2. ออกแบบโครงสร้างข้อมูลปลายทาง (Structured Output Schema) ด้วย Pydantic
class CargoSafetyResponse(BaseModel):
    item_name: str = Field(description="Name or category of the detected item (in Thai or English)")
    hazard_class: str = Field(description="Hazard class rating, e.g., 'Non-Hazardous' or 'Class 3 Flammable Liquid'")
    is_allowed: bool = Field(description="True if the item is approved for the selected transport method, False otherwise")
    handling_instructions: list[str] = Field(description="Precautions and instructions for warehouse workers on how to handle this package")
    storage_zone: str = Field(description="Recommended warehouse storage zone")

def run_cargo_scanner():
    print("=== AI ระบบตรวจสอบพัสดุและจัดหมวดหมู่ความปลอดภัยคลังสินค้า ===")
    
    # จำลองการโหลดภาพถ่ายพัสดุ
    image_path = 'cargo_item.jpg'
    if not os.path.exists(image_path):
        # สร้างภาพจำลองสีส้ม/แดง เพื่อเป็นตัวแทนสัญลักษณ์แจ้งเตือน
        img = Image.new('RGB', (200, 200), color = '#FF5722')
        img.save(image_path)
        print(f"[*] สร้างภาพจำลองสินค้าเรียบร้อยแล้ว: {image_path}")

    cargo_image = Image.open(image_path)

    # ----------------------------------------------------
    # ส่วนรับข้อมูลแบบ Dynamic Input จากผู้ใช้งาน (ภาษาไทย)
    # ----------------------------------------------------
    print("\n[ตั้งค่าข้อมูลการทดสอบ]")
    freight_method = input("ระบุวิธีการขนส่ง (เช่น Air Freight, Sea Freight, Road Freight): ")
    user_notes = input("บันทึกเพิ่มเติมจากเจ้าหน้าที่ (เช่น พบสัญลักษณ์เปลวไฟ, มีแบตเตอรี่ภายใน): ")
    print("----------------------------------------------------")

    # เตรียมข้อมูลนำเข้าสำหรับการประมวลผลรูปแบบ Multimodality
    contents = [
        cargo_image,
        f"Requested shipping method: {freight_method}",
        f"Operator notes: {user_notes}",
        "Please invoke check_shipping_regulations to cross-reference global restrictions before finalizing the analysis."
    ]

    # 3. กำหนดค่า Configuration สำหรับ AI (System Instruction, Tools, โครงสร้างข้อมูล)
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are an expert in industrial safety, dangerous goods compliance, and logistics operations. "
            "Your task is to analyze the cargo items. You must call the check_shipping_regulations tool to "
            "verify international transport restrictions based on the item type and freight method. "
            "You must strictly return the final output in the requested JSON schema format."
        ),
        temperature=0.1, # ใช้ค่าต่ำเพื่อให้ได้โครงสร้าง JSON ที่เสถียรและแม่นยำสูง
        tools=[check_shipping_regulations],
        response_mime_type="application/json",
        response_schema=CargoSafetyResponse,
    )

    print("\nกำลังส่งข้อมูลให้ AI ประมวลผลและตรวจสอบกฎระเบียบความปลอดภัย...")

    # 4. เรียกใช้โมเดลเพื่อประมวลผลพร้อมคำสั่ง Function Calling
    response = client.models.generate_content(
        model='gemini-3.6-flash', 
        contents=contents,
        config=config
    )

    # ----------------------------------------------------
    # ส่วนแปลงโครงสร้าง JSON ออกมาเป็นข้อความธรรมดาอ่านง่าย
    # ----------------------------------------------------
    try:
        # ดึง JSON string จากโครงสร้างการตอบกลับแล้วแปลงเป็น Dict
        data = json.loads(response.text)
        
        print(f"\n📦 ชื่อสินค้า: {data.get('item_name')}")
        print(f"⚠️ ระดับอันตราย: {data.get('hazard_class')}")
        
        status = "✅ ผ่าน (อนุญาตให้ขนส่ง)" if data.get('is_allowed') else "❌ ไม่ผ่าน (ไม่อนุญาตให้ขนส่ง)"
        print(f"🚦 สถานะการอนุมัติ: {status}")
        
        print(f"🏢 โซนจัดเก็บในคลัง: {data.get('storage_zone')}")
        print("📋 คำแนะนำในการจัดการความปลอดภัย:")
        for idx, instruction in enumerate(data.get('handling_instructions', []), 1):
            print(f"  {idx}. {instruction}")
            
    except Exception:
        # หากเกิดการตกหล่นของข้อมูลหรือ Error ป้องกันโปรแกรมพังด้วยการพิมพ์ดิบออกมาก่อน
        print(response.text)

    print("\n=== ตรวจสอบเสร็จสิ้น ระบบได้บันทึกข้อมูลเข้าคลังสินค้าเรียบร้อยแล้ว ===")

if __name__ == "__main__":
    run_cargo_scanner()