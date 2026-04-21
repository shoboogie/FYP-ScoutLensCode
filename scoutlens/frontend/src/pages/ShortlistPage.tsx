import { useAuth } from "../hooks/useAuth";
import { useShortlist, useRemoveFromShortlist, useUpdateShortlistNotes } from "../hooks/useShortlist";
import ShortlistEntryCard from "../components/shortlist/ShortlistEntry";
import NotesEditor from "../components/shortlist/NotesEditor";
import { Link } from "react-router-dom";

export default function ShortlistPage() {
  const { isAuthenticated } = useAuth();
  const { data, isLoading, isError } = useShortlist();
  const removeMutation = useRemoveFromShortlist();
  const updateNotesMutation = useUpdateShortlistNotes();

  if (!isAuthenticated) {
    return (
      <div className="text-center">
        <h1 className="mb-4 text-2xl font-bold text-navy">Shortlist</h1>
        <p className="mb-4 text-gray-500">Sign in to manage your scouting shortlist.</p>
        <Link
          to="/login"
          className="rounded bg-teal px-6 py-2 text-white hover:bg-teal-dark"
        >
          Sign In
        </Link>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-200" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        Failed to load shortlist.
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-navy">Shortlist</h1>
        <span className="text-sm text-gray-500">
          {data?.total ?? 0} player{data?.total !== 1 ? "s" : ""}
        </span>
      </div>

      {data && data.entries.length > 0 ? (
        <div className="space-y-3">
          {data.entries.map((entry) => (
            <div key={entry.id}>
              <ShortlistEntryCard
                entry={entry}
                onRemove={(id) => removeMutation.mutate(id)}
                onEditNotes={(id, notes) => updateNotesMutation.mutate({ id, notes })}
              />
              <NotesEditor
                initialNotes={entry.notes}
                onSave={(notes) => updateNotesMutation.mutate({ id: entry.id, notes })}
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg bg-gray-50 py-12 text-center">
          <p className="mb-2 text-gray-500">Your shortlist is empty</p>
          <Link to="/" className="text-sm text-teal hover:underline">
            Search for players to get started
          </Link>
        </div>
      )}
    </div>
  );
}
