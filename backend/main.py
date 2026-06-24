from fastapi import FastAPI, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from rag.rag_pipeline import retrieve_relevant_context
from database.db import engine
from database.db import Base
from database.db import SessionLocal
from database.models import Lead
import os
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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

    try:

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """

    You are a professional admissions counselor.

    Create a friendly and personalized follow-up message based on the lead summary.

    Guidelines:

    Use information from the lead summary.
    Mention the lead's interest or goal when relevant.
    Keep the tone warm and professional.
    Do not sound robotic.
    Do not sound salesy or pushy.
    Encourage further conversation naturally.
    Include at most one gentle call-to-action.
    Keep the message under 80 words.

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

    except Exception as e:

        print(f"Follow-up Generation Error: {e}")

        return (
            "Thank you for your interest. "
            "Please let us know if you have any questions. "
            "We would be happy to help."
        )


@app.get("/")
async def home():
    return {"message": "AI WhatsApp Assistant Running"}


def generate_ai_response(user_message, conversation_summary, lead):

    try:
        context = retrieve_relevant_context(user_message)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
            {
                "role": "system",
                "content": f"""

You are a professional AI admissions and customer support assistant.

You represent the organization described in the brochure information below.

Your job is to help prospective students or customers by providing accurate, useful, and complete information.

MEMORY

Use the Lead Information and Lead Summary to remember previous conversations and avoid asking the same questions repeatedly.

LEAD QUALIFICATION

Your first priority is gradually collecting these fields if they are missing:

Name
Email
Target Goal

IMPORTANT RULES

Always answer the user's question completely before asking for any missing information.
Never interrupt the conversation flow to collect information.
If information is missing, politely ask for it at the end of your response.
If all required information is already available, do not ask again.
Do not mention whether information has already been collected unless the user asks.

RESPONSE GUIDELINES

For greetings, acknowledgements, thanks, and casual conversation, keep responses concise.
For questions about courses, programs, curriculum, schedules, duration, fees, facilities, admissions, certifications, benefits, or any brochure-related information, provide complete and detailed answers.
If the user asks multiple questions, answer all of them.
If the user asks for details, provide details.
Never sacrifice important information just to keep responses short.
The quality and usefulness of the answer are more important than response length.

BROCHURE USAGE

The brochure information below is the official source of information.

Use it as your primary source when answering questions about:

Courses
Programs
Fees
Timings
Schedules
Duration
Curriculum
Admission Process
Facilities
Certifications
Benefits
Services

If relevant information exists in the brochure, provide a complete answer using that information.

HANDLING OBJECTIONS

If a user has concerns, doubts, or comparisons, address them professionally using facts available in the brochure.

Do not exaggerate.
Do not make unrealistic promises.
Do not pressure the user.

Your goal is to help the user make an informed decision.

Lead Information:

Name: {lead.name}
Email: {lead.email}
Target Goal: {lead.target_goal}

Lead Summary:

{conversation_summary}

Official Brochure Information:

{context}
"""
},
{
"role": "user",
"content": user_message
}
],
    temperature=0.3,
            max_tokens=600
        )

        return completion.choices[0].message.content

    except Exception as e:

        logger.error(f"AI Response Error: {e}")

        return (
            "Thank you for your message. "
            "Our admissions team will assist you shortly."
        ) 


def extract_lead_information(user_message):

    try:

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

        return json.loads(response_text)

    except Exception as e:

        print(f"Lead Extraction Error: {e}")

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

    try:
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

    except Exception as e:

        print(f"[ERROR] Conversation Summary Error: {e}")

        return old_summary

def calculate_lead_score(summary):

    try:

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

        return int(score_text.strip())

    except Exception as e:

        print(f"[ERROR] Lead Score Error: {e}")

        return 50
    

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

    logger.info(
        f"Message received from {phone_number}: {incoming_message}"
    )
    db = SessionLocal()

    lead = db.query(Lead).filter(
    Lead.phone_number == phone_number
    ).first()

    if not lead:

        lead = Lead(
            phone_number=phone_number
        )

        try:
            db.add(lead)

            db.commit()

            db.refresh(lead)

            logger.info(f"New lead created: {phone_number}")  #logging instaed of printing

        except Exception as e:
            db.rollback()

            # print(f"Database Error: {e}")
            logger.error(f"Database Error: {e}")

    else:

        logger.info(f"Existing lead found: {phone_number}")


    # print("MESSAGE RECEIVED:")
    # print(incoming_message)
    logger.info(f"MESSAGE RECEIVED: {incoming_message}")

    lead_data = extract_lead_information(incoming_message)

    logger.info(f"Lead information extracted for {phone_number}")

    try:
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

    except Exception as e:

        db.rollback()
        logger.error(f"Database Error: {e}")  #logged

    print("EXTRACTED DATA:")
    print(lead_data)

    updated_summary = generate_conversation_summary(
        lead.conversation_summary or "",
        incoming_message
    )

    try:

        lead.conversation_summary = updated_summary

        lead.lead_score = calculate_lead_score(
            lead.conversation_summary
        )

        logger.info(f"Lead score generated: {lead.lead_score}")

        lead.status = determine_status(
            lead.lead_score
        )

        db.commit()

    except Exception as e:

        db.rollback()

        print(f"Summary Update Error: {e}")

    print("UPDATED SUMMARY:")
    print(updated_summary)

    print("SUMMARY SENT TO AI:")
    print(lead.conversation_summary)

    # Generate AI response
    ai_reply = generate_ai_response(incoming_message, lead.conversation_summary or "", lead)

    # print("AI RESPONSE:")
    # print(ai_reply)
    logger.info(
    f"AI response generated for {phone_number}")

    # Twilio response
    twilio_response = MessagingResponse()

    twilio_response.message(ai_reply)

    db.close()

    return Response(
        content=str(twilio_response),
        media_type="application/xml"
    )
