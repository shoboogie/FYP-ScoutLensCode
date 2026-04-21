export default function Footer() {
  return (
    <footer className="bg-navy-dark py-4 text-center text-xs text-gray-400">
      <p>
        ScoutLens &copy; {new Date().getFullYear()} &mdash; BSc Computer Science
        Dissertation, University of Greenwich
      </p>
      <p className="mt-1">
        Data: StatsBomb Open Data (2015/16 Season)
      </p>
    </footer>
  );
}
