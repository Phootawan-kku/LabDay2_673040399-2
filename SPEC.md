# Specification: AI Cargo Scanner & Safety Classifier

## 1. Objective & Use Case
แอปพลิเคชันสำหรับธุรกิจ Logistics และการจัดการคลังสินค้า ช่วยคัดกรองพัสดุหรือสินค้าที่อาจเป็นอันตราย  และจัดหมวดหมู่สินค้าอัตโนมัติ โดยเจ้าหน้าที่สามารถถ่ายภาพตัวสินค้า/ป้ายกำกับ หรือพิมพ์รายละเอียด เพื่อให้ AI วิเคราะห์ความปลอดภัย ออกใบเตือน และจัดกลุ่มสินค้าลงฐานข้อมูลในรูปแบบ JSON Schema ที่แม่นยำ

## 2. Core Features (ฟีเจอร์จาก Lab)
1. **System Instructions:** กำหนดบทบาทให้เป็น "ผู้เชี่ยวชาญด้านความปลอดภัยวัตถุอันตรายและการจัดการโลจิสติกส์สากล"
2. **Structured Output (JSON):** บังคับให้ AI ส่งข้อมูลกลับมาเป็นโครงสร้าง JSON เพื่อให้ระบบคลังสินค้านำไปบันทึกลง Database ได้ทันที
3. **Multimodality:** รองรับการอัปโหลดภาพสินค้า ป้ายสัญลักษณ์เตือน เพื่อให้ AI ประมวลผล
4. **Function Calling (ฟีเจอร์เลือกเพิ่ม):** เชื่อมต่อกับระบบเช็คข้อจำกัดทางกฎหมายขนส่ง ตามประเภทของพัสดุ
5. **Streaming (โจทย์เสริม):** แสดงผลการคัดกรองแบบเรียลไทม์บนหน้าจอของเจ้าหน้าที่คลังสินค้าเพื่อความรวดเร็ว

## 3. Input / Output Design
- **Input:**
  - ภาพถ่ายสินค้า หรือ ป้ายสัญลักษณ์บนกล่อง 
  - ข้อมูลประเภทการขนส่ง เช่น "ทางอากาศ (Air Freight)" หรือ "ทางรถ (Road Freight)" (Text)
- **Output:** JSON Object ประกอบด้วย:
  - `item_name`: ชื่อหรือประเภทสินค้าที่ตรวจพบ
  - `hazard_class`: ระดับหรือประเภทวัตถุอันตราย (เช่น Non-Hazardous, Class 3 Flammable Liquid)
  - `is_allowed`: ผ่านเกณฑ์การขนส่งตามกฎหมายหรือไม่ (True/False)
  - `handling_instructions`: ข้อควรระวังในการจัดเก็บและเคลื่อนย้าย
  - `storage_zone`: โซนในคลังสินค้าที่แนะนำให้จัดเก็บ (เช่น Zone A:ทั่วไป, Zone HazMat:วัตถุอันตราย)

## 4. Prompt Engineering & System Instruction
- **System Instruction:**
  "You are an expert in industrial safety, dangerous goods compliance (IATA/IMDG), and logistics operations. Your task is to analyze the provided image or text description of cargo items. You must call the `check_shipping_regulations` tool to verify if the item class has specific restrictions for the chosen freight type. Return the assessment strictly in the requested JSON format."
- **User Prompt Template:**
  "ตรวจสอบความปลอดภัยของพัสดุชิ้นนี้ [Image/Text] สำหรับการขนส่งรูปแบบ: [Freight Type]"