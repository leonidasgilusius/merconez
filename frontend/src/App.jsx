import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import HomePage from "./pages/HomePage";
import TranslatePage from "./pages/TranslatePage";

function App() {
  return (
    <Router>
      <nav style={{ padding: "1rem", background: "#eee" }}>
        <Link to="/" style={{ marginRight: "1rem" }}>Home</Link>
        <Link to="/translate">Translate</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/translate" element={<TranslatePage />} />
      </Routes>
    </Router>
  );
}

export default App;
