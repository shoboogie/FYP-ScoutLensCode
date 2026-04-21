import { useState } from "react";

interface Props {
  initialNotes: string;
  onSave: (notes: string) => void;
}

export default function NotesEditor({ initialNotes, onSave }: Props) {
  const [notes, setNotes] = useState(initialNotes);
  const [editing, setEditing] = useState(false);

  const handleSave = () => {
    onSave(notes);
    setEditing(false);
  };

  if (!editing) {
    return (
      <button
        onClick={() => setEditing(true)}
        className="text-xs text-teal hover:underline"
      >
        {initialNotes ? "Edit notes" : "Add notes"}
      </button>
    );
  }

  return (
    <div className="mt-2 space-y-2">
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        rows={3}
        placeholder="Scouting notes..."
        className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
      />
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          className="rounded bg-teal px-3 py-1 text-xs text-white hover:bg-teal-dark"
        >
          Save
        </button>
        <button
          onClick={() => setEditing(false)}
          className="rounded px-3 py-1 text-xs text-gray-500 hover:bg-gray-100"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
