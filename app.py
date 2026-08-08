import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# โหลด Environment Variables
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("กรุณาตั้งค่า GEMINI_API_KEY ในไฟล์ .env ก่อนเริ่มงาน")

# สร้าง Client
client = genai.Client()

# 1. กำหนด Mock Tool สำหรับ Function Calling
def check_shipping_regulations(item_type: str, freight_method: str) -> dict:
    """ตรวจสอบข้อจำกัดและข้อห้ามทางกฎหมายในการขนส่งตามประเภทสินค้าและรูปแบบการขนส่ง"""
    # จำลองว่าถ้าส่งทางอากาศ (Air) และเป็นวัตถุไวไฟ/แก๊สแรงดัน จะไม่อนุญาต
    if "air" in freight_method.lower() and ("flammable" in item_type.lower() or "spray" in item_type.lower()):
        return {"status": "RESTRICTED", "reason": "สารไวไฟและวัตถุแรงดันสูงห้ามขนส่งทางอากาศตามกฎระเบียบ IATA"}
    return {"status": "APPROVED", "reason": "ไม่พบข้อจำกัดรุนแรงในรูปแบบการขนส่งนี้"}

# 2. ออกแบบ Structured Output Schema ด้วย Pydantic
class CargoSafetyResponse(BaseModel):
    item_name: str = Field(description="ชื่อหรือประเภทสินค้าภาษาไทยที่ระบบตรวจพบ")
    hazard_class: str = Field(description="ระดับหรือประเภทวัตถุอันตราย เช่น Non-Hazardous หรือ Class 3 Flammable Liquid")
    is_allowed: bool = Field(description="ผลการตรวจสอบว่าอนุญาตให้ขนส่งในรูปแบบที่เลือกหรือไม่ (true/false)")
    handling_instructions: list[str] = Field(description="ข้อควรระวังและวิธีปฏิบัติในการเคลื่อนย้ายพัสดุชิ้นนี้")
    storage_zone: str = Field(description="โซนจัดเก็บที่แนะนำในคลังสินค้า")

def run_cargo_scanner():
    print("===ระบบ AI ตรวจสอบพัสดุและจัดหมวดหมู่ความปลอดภัยคลังสินค้า ===")
    
    # จำลองการโหลดรูปภาพพัสดุ/สินค้า
    image_path = 'cargo_item.jpg'
    if not os.path.exists(image_path):
        # สร้างภาพสีแดงจำลองสัญลักษณ์เตือนภัยไฟไหม้
        img = Image.new('RGB', (200, 200), color = '#FF5722')
        img.save(image_path)
        print(f"[*] สร้างภาพจำลองสินค้า {image_path} เรียบร้อยแล้ว")

    cargo_image = Image.open(image_path)
    freight_method = "Air Freight (ขนส่งทางเครื่องบิน)"
    user_notes = "พบป้ายสัญลักษณ์รูปเปลวไฟบนกล่องบรรจุภัณฑ์"

    # รวม Input ทั้งหมด
    contents = [
        cargo_image,
        f"รูปแบบการขนส่งที่ต้องการ: {freight_method}",
        f"บันทึกเพิ่มเติมจากเจ้าหน้าที่: {user_notes}",
        "โปรดใช้เครื่องมือ check_shipping_regulations โดยระบุผลวิเคราะห์เบื้องต้นและรูปแบบขนส่งเพื่อตรวจสอบกฎข้อบังคับ"
    ]

    # 3. กำหนด Config (System Instruction, Tools, Temperature ต่ำ, Schema)
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are an expert in industrial safety, dangerous goods compliance, and logistics operations. "
            "Your task is to analyze the cargo items. You must call the check_shipping_regulations tool to "
            "verify international transport restrictions based on the item type and freight method. "
            "You must strictly return the final output in the requested JSON schema format."
        ),
        temperature=0.1, # ตั้งไว้ต่ำสุดๆ เพื่อเน้นความถูกต้อง ป้องกัน AI มโนข้อกฎหมาย
        tools=[check_shipping_regulations],
        response_mime_type="application/json",
        response_schema=CargoSafetyResponse,
    )

    print("\nกำลังส่งให้ AI ประมวลผลและตรวจสอบกฎระเบียบ...")
    print("--- ผลลัพธ์แบบ Streaming JSON ---")

    # 4. เรียกใช้การ Stream ผลลัพธ์
    response_stream = client.models.generate_content_stream(
        model='gemini-2.5-flash',
        contents=contents,
        config=config
    )

    for chunk in response_stream:
        print(chunk.text, end="", flush=True)

    print("\n\n=== ตรวจสอบเสร็จสิ้น บันทึกข้อมูลเข้าคลังสินค้าเรียบร้อย ===")

if __name__ == "__main__":
    run_cargo_scanner()