import Link from "next/link";
async function getLeads() {
  const res = await fetch("http://127.0.0.1:8000/leads", {
    cache: "no-store",
  });

  return res.json();
}

async function getStats() {
  const res = await fetch("http://127.0.0.1:8000/dashboard-stats", {
    cache: "no-store",
  });

  return res.json();
}

export default async function Dashboard() {
  const leads = await getLeads();
  leads.sort((a: any, b: any) => (b.lead_score || 0) - (a.lead_score || 0));

  const stats = await getStats();

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold mb-2 text-gray-800">
        AI Admissions CRM
      </h1>

      {/* <p className="text-gray-500 mb-8 font-sans"> */}
      <p className="text-gray-400 mb-12 font-sans font-light tracking-wide">
        AI-powered lead management and admissions automation
      </p>

      <h2 className="text-xl font-semibold text-gray-700 mb-4">
        Lead Pipeline
      </h2>
      <div className="grid grid-cols-3 gap-6 mb-10">
        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-gray-600">Total Leads</h3>

          <p className="text-3xl font-bold text-gray-500">
            {stats.total_leads}
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-gray-600">Hot Leads</h3>

          <p className="text-3xl font-bold text-green-600">{stats.hot_leads}</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-lg">
          <h3 className="text-gray-600">Average Score</h3>

          <p className="text-3xl font-bold text-gray-500">
            {stats.average_score}
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-200">
              <th className="text-left p-4 text-gray-600">Name</th>

              <th className="text-left p-4 text-gray-600">Status</th>

              <th className="text-left p-4 text-gray-600">City</th>

              <th className="text-left p-4 text-gray-600">Course</th>

              <th className="text-left p-4 text-gray-600">Score</th>

              <th className="text-left p-4 text-gray-600">Action</th>

              <th className="text-left p-4 text-gray-600">Updated</th>
            </tr>
          </thead>

          <tbody>
            {leads.map((lead: any) => (
              <tr key={lead.id} className="border-t hover:bg-gray-50">
                <td className="p-4">
                  <Link
                    href={`/dashboard/${lead.id}`}
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {lead.name || "Not Provided"}
                  </Link>
                </td>

                <td className="p-4">
                  <span
                    className={
                      lead.status === "NEW"
                        ? "bg-gray-200 text-gray-800 px-3 py-1 rounded-full text-sm"
                        : lead.status === "CONTACTED"
                          ? "bg-blue-200 text-blue-800 px-3 py-1 rounded-full text-sm"
                          : lead.status === "INTERESTED"
                            ? "bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm"
                            : lead.status === "ENROLLED"
                              ? "bg-purple-200 text-purple-800 px-3 py-1 rounded-full text-sm"
                              : "bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm"
                    }
                  >
                    {lead.status}
                  </span>
                </td>

                <td className="p-4 text-gray-600">{lead.city}</td>

                <td className="p-4 text-gray-600">{lead.course_interest}</td>

                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        lead.lead_score >= 80
                          ? "bg-green-500"
                          : lead.lead_score >= 50
                            ? "bg-yellow-500"
                            : "bg-red-500"
                      }`}
                    />

                    <span className="font-semibold text-gray-700">
                      {lead.lead_score}
                    </span>
                  </div>
                </td>
                <td className="p-4 text-gray-600">
                  {lead.lead_score >= 80
                    ? "🔥 Call"
                    : lead.lead_score >= 50
                      ? "📞 Follow Up"
                      : "✉️ Nurture"}
                </td>

                <td className="p-4 text-gray-500">
                  {new Date(lead.updated_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
