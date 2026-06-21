import Link from "next/link";
import CopyButton from "@/app/components/CopyButton";

async function getLead(id: string) {
  const res = await fetch(`http://127.0.0.1:8000/leads/${id}`, {
    cache: "no-store",
  });

  return res.json();
}

export default async function LeadDetails({ params }: any) {
  const { id } = await params;

  const lead = await getLead(id);

  console.log(lead);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-5xl mx-auto">
        <Link
          href="/dashboard"
          className="text-blue-600 hover:underline flex justify-end"
        >
          ← Back to Dashboard
        </Link>
        <h1 className="text-4xl font-bold mb-8 text-gray-800">Lead Profile</h1>
        <div className="bg-white rounded-xl shadow p-6 mb-8">
          <h2 className="text-4xl font-bold text-gray-800">{lead.name}</h2>
          <p className="text-gray-500 mt-2">AI Qualified Lead</p>

          <div className="flex gap-8 text-sm text-gray-600 mt-4">
            {lead.city && <p>📍 {lead.city}</p>}

            {lead.phone_number && <p>📞 {lead.phone_number}</p>}

            {lead.target_goal && <p>🎯 {lead.target_goal}</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow p-8">
          <div className="grid grid-cols-2 gap-6">
            {/* <div>
              <p className="text-gray-600">Name</p>
              <p className="text-xl font-semibold text-gray-600">{lead.name}</p>
            </div> */}

            {/* <div>
              <p className="text-gray-600">Phone</p>
              <p className="text-xl font-semibold text-gray-600">
                {lead.phone_number}
              </p>
            </div> */}

            <div>
              <p className="text-gray-600">Email</p>
              <p className="text-xl font-semibold text-gray-600">
                {lead.email || "Not Provided"}
              </p>
            </div>

            <div>
              <p className="text-gray-600">City</p>
              <p className="text-xl font-semibold text-gray-600">
                {lead.city || "Not Provided"}
              </p>
            </div>

            <div>
              <p className="text-gray-600">Target Goal</p>
              <p className="text-xl font-semibold text-gray-600">
                {lead.target_goal}
              </p>
            </div>

            <div>
              <p className="text-gray-600">Course Interest</p>
              <p className="text-xl font-semibold text-gray-600">
                {lead.course_interest}
              </p>
            </div>
          </div>

          <hr className="my-8" />

          <div className="grid grid-cols-2 gap-6 mb-8">
            <div className="bg-green-50 p-6 rounded-xl">
              <p className="text-gray-600 mb-2">Lead Score</p>

              <p className="text-4xl font-bold text-green-600">
                {lead.lead_score} / 100
              </p>
            </div>

            <div className="bg-blue-50 p-6 rounded-xl">
              <p className="text-gray-600 mb-2">Status</p>

              <span
                className={`px-4 py-2 rounded-full font-semibold ${
                  lead.status === "NEW"
                    ? "bg-gray-100 text-gray-600"
                    : lead.status === "CONTACTED"
                      ? "bg-blue-100 text-blue-700"
                      : lead.status === "INTERESTED"
                        ? "bg-green-100 text-green-700"
                        : lead.status === "ENROLLED"
                          ? "bg-purple-100 text-purple-700"
                          : "bg-red-100 text-red-700"
                }`}
              >
                {lead.status}
              </span>
            </div>
          </div>

          <div className="bg-orange-50 border-l-4 border-orange-500 p-6 rounded-xl mb-8">
            <p className="text-sm text-gray-500 mb-2">Recommended Action</p>

            <p className="text-2xl font-bold text-orange-600">
              <span
                className={
                  lead.recommended_action.includes("Call")
                    ? "text-red-600"
                    : "text-orange-600"
                }
              >
                {lead.recommended_action}
              </span>
            </p>
          </div>

          <div className="bg-white shadow rounded-xl p-6 mb-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-700">
              📝 Conversation Summary
            </h2>

            <div className="text-gray-600 whitespace-pre-wrap leading-relaxed">
              {lead.conversation_summary}
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-bold mb-4 text-gray-600">
              🤖 AI Generated Follow-Up
            </h2>

            <div className="bg-blue-50 p-6 rounded-xl text-gray-700 shadow-sm">
              <p className="mb-4 whitespace-pre-wrap">
                {lead.followup_message}
              </p>

              <CopyButton message={lead.followup_message} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
