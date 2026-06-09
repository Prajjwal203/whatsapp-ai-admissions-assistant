async function getLeads() {
  const res = await fetch("http://localhost:8000/leads", {
    cache: "no-store",
  });

  return res.json();
}

export default async function Dashboard() {
  const leads = await getLeads();

  return (
    <div style={{ padding: "30px" }}>
      <h1>AI Admissions Dashboard</h1>

      <br />

      <table
        style={{
          borderCollapse: "collapse",
          width: "100%",
        }}
      >
        <thead>
          <tr>
            <th style={{ border: "1px solid gray", padding: "10px" }}>Name</th>

            <th style={{ border: "1px solid gray", padding: "10px" }}>City</th>

            <th style={{ border: "1px solid gray", padding: "10px" }}>
              Course
            </th>

            <th style={{ border: "1px solid gray", padding: "10px" }}>Score</th>
          </tr>
        </thead>

        <tbody>
          {leads.map((lead: any) => (
            <tr key={lead.id}>
              <td style={{ border: "1px solid gray", padding: "10px" }}>
                {lead.name}
              </td>

              <td style={{ border: "1px solid gray", padding: "10px" }}>
                {lead.city}
              </td>

              <td style={{ border: "1px solid gray", padding: "10px" }}>
                {lead.course_interest}
              </td>

              <td style={{ border: "1px solid gray", padding: "10px" }}>
                {lead.lead_score}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
