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


# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

app = FastAPI()

def get_recommended_action(score):

    if score >= 80:
        return "🔥 Call Immediately"

    elif score >= 60:
        return "📞 Follow Up Today"

    elif score >= 30:
        return "✉️ Send Follow-Up Message"

    else:
        return "🕒 Low Priority"
    

def generate_followup_message(summary):

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """
You are an admissions counselor.

Create a short, friendly follow-up message.

Use the lead summary.

Keep it under 80 words.

Do not be pushy.

Return ONLY the follow-up message.
"""
            },
            {
                "role": "user",
                "content": summary
            }
        ],
        temperature=0.5,
        max_tokens=150
    )

    return completion.choices[0].message.content

@app.get("/")
async def home():
    return {"message": "AI WhatsApp Assistant Running"}


def generate_ai_response(user_message, conversation_summary, lead):

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

                    "Your first priority is collecting these fields:\n"
                    "1. Name\n"
                    "2. Email\n"
                    "3. Target Goal\n\n"

                    "If any of these fields are missing, answer the user's question normally, but politely ask for the missing information at the end.\n\n"

                    "If all three fields are already available, do not ask again.\n\n"
                    "Do not tell the customer whether you have got their fields or not, unless they directly or indirectly ask, just register them and remember everything.\n\n"
                    "Convince the customer if he/she doesn't feel like the Institute's course is good enough for him/her. Make him/her believe how FluentFast Academy can be the best option.\n\n"

                    "Never interrupt the conversation.\n"
                    "Always answer the user's question first.\n"
                    "Keep the replies under 80 words for general talking, but there's no word limit when you're providing any important info.\n"

                    "Use the lead summary to remember previous interactions.\n\n"

                    f"""
                        Lead Information:

                        Name: {lead.name}
                        Email: {lead.email}
                        Target Goal: {lead.target_goal}

                        Lead Summary:
                        {conversation_summary}

                        Brochure Information:
                        {context}
                    """
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
You are an expert admissions counselor and CRM analyst.

Analyze the lead summary and estimate the student's likelihood of enrolling.

Return ONLY a number between 0 and 100.

Scoring Guide:

0-20 = Casual visitor with little interest
21-40 = Exploring options
41-60 = Interested prospect
61-80 = Serious prospect
81-100 = Highly likely to enroll

Positive signals:

- asking about fees
- asking about enrollment
- asking about batch timings
- asking about curriculum
- asking about certification
- asking about admission process
- discussing start dates
- prior qualifications related to the course
- sharing email or contact information
- expressing urgency
- expressing strong interest
- asking multiple detailed questions

Negative signals:

- just browsing
- just exploring
- comparing multiple institutes
- not ready yet
- maybe later
- no clear goal
- vague interest
- curiosity without intent

Important:

Do NOT increase the score simply because the conversation is long.

Focus on enrollment intent and buying intent.

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
    

def determine_status(score):

    if score >= 80:
        return "INTERESTED"

    elif score >= 40:
        return "CONTACTED"

    else:
        return "NEW"

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
            "status": lead.status,
            "conversation_summary": lead.conversation_summary,
            "lead_score": lead.lead_score,
            "updated_at": lead.updated_at,
        })

    db.close()

    return result

@app.get("/leads/{lead_id}")
async def get_lead(lead_id: int):

    db = SessionLocal()

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    if not lead:
        db.close()
        return {"error": "Lead not found"}

    followup_message = generate_followup_message(
        lead.conversation_summary or ""
    )

    db.close()

    return {
    "id": lead.id,
    "name": lead.name,
    "phone_number": lead.phone_number,
    "email": lead.email,
    "city": lead.city,
    "target_goal": lead.target_goal,
    "course_interest": lead.course_interest,
    "status": lead.status,
    "conversation_summary": lead.conversation_summary,
    "lead_score": lead.lead_score,
    "updated_at": lead.updated_at,
    "recommended_action": get_recommended_action(
        lead.lead_score or 0
    ),
    "followup_message": followup_message
}

@app.get("/dashboard-stats")
async def dashboard_stats():

    db = SessionLocal()

    leads = db.query(Lead).all()

    total_leads = len(leads)

    hot_leads = len([
        lead for lead in leads
        if (lead.lead_score or 0) >= 80
    ])

    average_score = 0

    if total_leads > 0:

        average_score = sum(
            lead.lead_score or 0
            for lead in leads
        ) / total_leads

    db.close()

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "average_score": round(average_score, 2)
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

    lead.lead_score = calculate_lead_score(
        lead.conversation_summary
    )

    lead.status = determine_status(
        lead.lead_score
    )

    print("CURRENT LEAD SCORE:")
    print(lead.lead_score)

    print("CURRENT STATUS:")
    print(lead.status)

    db.commit()

    print("UPDATED SUMMARY:")
    print(updated_summary)

    print("SUMMARY SENT TO AI:")
    print(lead.conversation_summary)

    # Generate AI response
    ai_reply = generate_ai_response(incoming_message, lead.conversation_summary or "", lead)

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
