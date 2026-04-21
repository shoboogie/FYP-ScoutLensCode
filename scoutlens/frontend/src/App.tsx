import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./context/AuthContext";
import Layout from "./components/layout/Layout";
import SearchPage from "./pages/SearchPage";
import PlayerProfilePage from "./pages/PlayerProfilePage";
import SimilarityResultsPage from "./pages/SimilarityResultsPage";
import ShortlistPage from "./pages/ShortlistPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={<SearchPage />} />
              <Route path="/player/:id" element={<PlayerProfilePage />} />
              <Route path="/similar/:id" element={<SimilarityResultsPage />} />
              <Route path="/shortlist" element={<ShortlistPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
