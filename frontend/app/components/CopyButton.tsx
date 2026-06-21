"use client";

export default function CopyButton({ message }: { message: string }) {
  const copyMessage = async () => {
    await navigator.clipboard.writeText(message);

    alert("Message copied!");
  };

  return (
    <button
      onClick={copyMessage}
      className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
    >
      Copy Message
    </button>
  );
}
