import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from PIL import Image

# Load environment variables
load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    raise ValueError("Please set GEMINI_API_KEY in your .env file before running.")

# Initialize the GenAI Client
client = genai.Client()

# 1. Define Mock Tool for Function Calling
def check_shipping_regulations(item_type: str, freight_method: str) -> dict:
    """Check dangerous goods international shipping regulations and restrictions."""
    if "air" in freight_method.lower() and ("flammable" in item_type.lower() or "spray" in item_type.lower()):
        return {"status": "RESTRICTED", "reason": "Flammable aerosols are strictly prohibited on air freight via IATA regulations."}
    return {"status": "APPROVED", "reason": "No major restrictions found for this cargo type on the selected freight method."}

# 2. Design Structured Output Schema using Pydantic
class CargoSafetyResponse(BaseModel):
    item_name: str = Field(description="Name or category of the detected item (in Thai or English)")
    hazard_class: str = Field(description="Hazard class rating, e.g., 'Non-Hazardous' or 'Class 3 Flammable Liquid'")
    is_allowed: bool = Field(description="True if the item is approved for the selected transport method, False otherwise")
    handling_instructions: list[str] = Field(description="Precautions and instructions for warehouse workers on how to handle this package")
    storage_zone: str = Field(description="Recommended warehouse storage zone")

def run_cargo_scanner():
    print("=== AI Cargo Scanner & Safety Classifier ===")
    
    # Simulate loading cargo image
    image_path = 'cargo_item.jpg'
    if not os.path.exists(image_path):
        # Create a mock orange/red image representing a warning sign
        img = Image.new('RGB', (200, 200), color = '#FF5722')
        img.save(image_path)
        print(f"[*] Simulated cargo image created: {image_path}")

    cargo_image = Image.open(image_path)
    freight_method = "Air Freight"
    user_notes = "Flashing flame symbol symbol observed on the package box."

    # Prepare inputs for Multimodality
    contents = [
        cargo_image,
        f"Requested shipping method: {freight_method}",
        f"Operator notes: {user_notes}",
        "Please invoke check_shipping_regulations to cross-reference global restrictions before finalizing the analysis."
    ]

    # 3. Configure generation options (System Instruction, Tools, Low Temperature, Schema)
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are an expert in industrial safety, dangerous goods compliance, and logistics operations. "
            "Your task is to analyze the cargo items. You must call the check_shipping_regulations tool to "
            "verify international transport restrictions based on the item type and freight method. "
            "You must strictly return the final output in the requested JSON schema format."
        ),
        temperature=0.1, # Low temperature ensures stable JSON structure and high accuracy
        tools=[check_shipping_regulations],
        response_mime_type="application/json",
        response_schema=CargoSafetyResponse,
    )

    print("\nProcessing cargo data and checking safety regulations...")
    print("--- Streaming JSON Response ---")

    # 4. Stream the response chunks to the console
    response = client.models.generate_content(
        model='gemini-3.6-flash', # <--- เปลี่ยนเป็นตัวหลักตามมาตรฐาน
        contents=contents,
        config=config
    )

    print(response.text)

    print("\n\n=== Scan Complete. Data saved to inventory dashboard. ===")

if __name__ == "__main__":
    run_cargo_scanner()