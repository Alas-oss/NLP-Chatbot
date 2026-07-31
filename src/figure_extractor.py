from pdf2image import convert_from_path
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
import base64
from io import BytesIO

vision_model = init_chat_model("groq:llama-3.2-90db-vision preview")

def describe_figures(pdf_path: str, pages: list[int]) -> list[dict]:
    images = convert_from_path(pdf_path)
    descripitons = []
    for page_num in pages:
        img = images[page_num]
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        response = vision_model.invoke([
            HumanMessage(content=[
                {"type": "text", "text": "Describe any charts, graphs, or figures on this page factually, including approximate values shown."},
                {"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
            ])
        ])
        descripitons.append({"page": page_num + 1, "description": response.content})
    return descripitons
