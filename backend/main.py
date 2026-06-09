from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from rag.rag_pipeline import retrieve_relevant_context
from database.db import engine
from database.db import Base
from database.db import SessionLocal
from database.models import Lead
import os
import json

Base.metadata.create_all(bind=engine)

from groq import Groq
from dotenv import load_dotenv

import os

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = FastAPI()


@app.get("/")
async def home():
    return {"message": "AI WhatsApp Assistant Running"}


def generate_ai_response(user_message, conversation_summary):

    context = retrieve_relevant_context(user_message)

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional AI admissions assistant "
                    "for a coaching institute.\n\n"

                    "Use the lead summary to remember previous interactions.\n\n"

                    f"Lead Summary:\n{conversation_summary}\n\n"

                    f"Brochure Information:\n{context}"
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
temperature=0.3,
        max_tokens=300
    )

    return completion.choices[0].message.content


def extract_lead_information(user_message):

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
Extract lead information from the message.

Return ONLY valid JSON.

Fields:
name
email
city
target_goal
course_interest

If a field is missing, return null.
"""
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        temperature=0
    )

    response_text = completion.choices[0].message.content

    print("RAW EXTRACTION RESPONSE:")
    print(response_text)

    response_text = response_text.replace("```json", "")
    response_text = response_text.replace("```", "")
    response_text = response_text.strip()

    try:
        return json.loads(response_text)

    except Exception as e:

        print("JSON ERROR:")
        print(e)

        return {
            "name": None,
            "email": None,
            "city": None,
            "target_goal": None,
            "course_interest": None
        }

def generate_conversation_summary(
    old_summary,
    new_message
):

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are a CRM assistant.

Update the existing conversation summary using the new message.

Keep the summary concise.

Include:
- student's goals
- interests
- location
- questions asked
- important details

Return ONLY the updated summary.
"""
            },
            {
                "role": "user",
                "content": f"""
Current Summary:
{old_summary}

New Message:
{new_message}
"""
            }
        ],
        temperature=0.2,
        max_tokens=200
    )

    return completion.choices[0].message.content

def calculate_lead_score(summary):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are an admissions counselor.

Analyze the lead summary.

Return ONLY a number between 0 and 100.

Scoring Guide:

0-20 = Cold Lead
21-50 = Warm Lead
51-80 = Hot Lead
81-100 = Ready To Enroll

Consider:

- interest level
- questions asked
- course inquiries
- prior qualifications
- enrollment intent
- contact details shared

Return ONLY the number.
"""
            },
            {
                "role": "user",
                "content": summary
            }
        ],
        temperature=0
    )

    score_text = completion.choices[0].message.content

    try:
        return int(score_text.strip())

    except:
        return 0

@app.get("/leads")
async def get_leads():

    db = SessionLocal()

    leads = db.query(Lead).all()

    result = []

    for lead in leads:

        result.append({
            "id": lead.id,
            "name": lead.name,
            "phone_number": lead.phone_number,
            "email": lead.email,
            "city": lead.city,
            "target_goal": lead.target_goal,
            "course_interest": lead.course_interest,
            "conversation_summary": lead.conversation_summary,
            "lead_score": lead.lead_score
        })

    db.close()

    return result

@app.get("/leads/{lead_id}")
async def get_lead(lead_id: int):

    db = SessionLocal()

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    db.close()

    if not lead:
        return {"error": "Lead not found"}

    return {
        "id": lead.id,
        "name": lead.name,
        "phone_number": lead.phone_number,
        "email": lead.email,
        "city": lead.city,
        "target_goal": lead.target_goal,
        "course_interest": lead.course_interest,
        "conversation_summary": lead.conversation_summary,
        "lead_score": lead.lead_score
    }

@app.post("/webhook")
async def whatsapp_webhook(request: Request):

    form_data = await request.form()

    incoming_message = form_data.get("Body")

    phone_number = form_data.get("From")
    db = SessionLocal()

    lead = db.query(Lead).filter(
    Lead.phone_number == phone_number
    ).first()

    if not lead:

        lead = Lead(
            phone_number=phone_number
        )

        db.add(lead)

        db.commit()

        db.refresh(lead)

        print("NEW LEAD CREATED")

    else:

        print("EXISTING LEAD FOUND")


    print("MESSAGE RECEIVED:")
    print(incoming_message)

    lead_data = extract_lead_information(incoming_message)

    if lead_data.get("name"):
        lead.name = lead_data["name"]

    if lead_data.get("email"):
        lead.email = lead_data["email"]

    if lead_data.get("city"):
        lead.city = lead_data["city"]

    if lead_data.get("target_goal"):
        lead.target_goal = lead_data["target_goal"]

    if lead_data.get("course_interest"):
        lead.course_interest = lead_data["course_interest"]

    db.commit()

    print("EXTRACTED DATA:")
    print(lead_data)

    updated_summary = generate_conversation_summary(
        lead.conversation_summary or "",
        incoming_message
    )

    lead.conversation_summary = updated_summary

    lead.lead_score += calculate_lead_score(
        incoming_message
    )

    print("CURRENT LEAD SCORE:")
    print(lead.lead_score)

    db.commit()

    print("UPDATED SUMMARY:")
    print(updated_summary)

    print("SUMMARY SENT TO AI:")
    print(lead.conversation_summary)

    # Generate AI response
    ai_reply = generate_ai_response(incoming_message, lead.conversation_summary or "")

    print("AI RESPONSE:")
    print(ai_reply)

    # Twilio response
    twilio_response = MessagingResponse()

    twilio_response.message(ai_reply)

    db.close()

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )
