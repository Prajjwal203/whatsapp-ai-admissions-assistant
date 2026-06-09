async function getLead(id: string) {
  const res = await fetch(`http://localhost:8000/leads/${id}`, {
    cache: "no-store",
  });

  return res.json();
}

export default async function LeadDetails({ params }: any) {
  const { id } = await params;

  const lead = await getLead(id);

  console.log(lead);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Lead Details</h1>

      <hr />

      <p>
        <b>Name:</b> {lead.name}
      </p>

      <p>
        <b>Phone:</b> {lead.phone_number}
      </p>

      <p>
        <b>Email:</b> {lead.email}
      </p>

      <p>
        <b>City:</b> {lead.city}
      </p>

      <p>
        <b>Target Goal:</b> {lead.target_goal}
      </p>

      <p>
        <b>Course Interest:</b> {lead.course_interest}
      </p>

      <p>
        <b>Lead Score:</b> {lead.lead_score}
      </p>

      <br />

      <h3>Conversation Summary</h3>

      <p>{lead.conversation_summary}</p>
    </div>
  );
}
