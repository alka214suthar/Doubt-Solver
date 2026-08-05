import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import MainLayout from "./Layouts/MainLayout";

import Login from "./pages/Login";
import Register from "./pages/Register";
import AskDoubt from "./pages/AskDoubt";
import History from "./pages/History";
import Bookmarks from "./pages/Bookmarks";
import DoubtDetails from "./pages/DoubtDetails";
import Profile from "./pages/Profile";

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 3000,
          style: {
            borderRadius: "14px",
            background: "#ffffff",
            color: "#1e293b",
            padding: "14px 18px",
            boxShadow: "0 12px 30px rgba(15, 23, 42, 0.18)",
          },
          success: {
            iconTheme: {
              primary: "#22c55e",
              secondary: "#ffffff",
            },
          },
          error: {
            duration: 3500,
            iconTheme: {
              primary: "#ef4444",
              secondary: "#ffffff",
            },
          },
        }}
      />
      <Routes>

        {/* Login Routes */}

        <Route path="/" element={<Login />} />

        <Route path="/register" element={<Register />} />

        {/* Routes With Navbar */}

        <Route element={<MainLayout />}>

          <Route path="/ask-doubt" element={<AskDoubt />} />

          <Route path="/history" element={<History />} />

          <Route path="/bookmarks" element={<Bookmarks />} />

          <Route path="/profile" element={<Profile />} />

          <Route path="/doubt" element={<DoubtDetails />} />

        </Route>

      </Routes>
    </BrowserRouter>
  );
}

export default App;