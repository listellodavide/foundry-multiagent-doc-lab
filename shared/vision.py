"""Vision extraction for scanned pages: the page is rendered to PNG and sent to the model.

Uses the OpenAI client exposed by the Foundry project (Responses API) with structured output,
so the result is a validated VendorProfile, not free text.
"""

import base64

from shared import config
from shared.clients import project_client
from shared.pdf import render_page_png
from shared.schema import VendorProfile

PROMPT = (
    "This is a scanned company profile from a vendor onboarding packet. Extract the registered "
    "legal name, trade register number, country, the authorised signatory, and only the last 4 "
    "characters of the IBAN. Use null for anything you cannot read. Do not guess."
)


def extract_profile_from_scan(file: str = "06_company_profile_scan.pdf", page: int = 1) -> VendorProfile:
    image = base64.b64encode(render_page_png(file, page)).decode()
    with project_client() as project, project.get_openai_client() as openai_client:
        response = openai_client.responses.parse(
            model=config.MODEL,
            input=[{"role": "user", "content": [
                {"type": "input_text", "text": PROMPT},
                {"type": "input_image", "image_url": f"data:image/png;base64,{image}", "detail": "high"},
            ]}],
            text_format=VendorProfile,
        )
    return response.output_parsed
