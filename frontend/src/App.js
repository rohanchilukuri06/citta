import { BrowserRouter, Routes, Route } from "react-router-dom";
import "@/App.css";
import Home from "@/pages/Home";
import Contact from "@/pages/Contact";
import Recognition from "@/pages/Recognition";
import CaseStudies from "@/pages/CaseStudies";
import About from "@/pages/About";
import Services from "@/pages/Services";
import ServiceSubPage from "@/pages/ServiceSubPage";
import PSPage from "@/pages/PSPage";
import AdminConsultant from "@/pages/AdminConsultant";
import SceneGallery from "@/pages/SceneGallery";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import BackToTop from "@/components/BackToTop";
import AIConsultant from "@/components/AIConsultant";
import ScrollToTop from "@/components/ScrollToTop";

function App() {
  return (
    <div className="App min-h-screen">
      <BrowserRouter>
        <ScrollToTop />
        <Navbar />
        <main id="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products/:slug" element={<PSPage kind="product" />} />
            <Route path="/solutions/:slug" element={<PSPage kind="solution" />} />
            <Route path="/services" element={<Services />} />
            <Route path="/services/:slug" element={<ServiceSubPage />} />
            <Route path="/recognition" element={<Recognition />} />
            <Route path="/case-studies" element={<CaseStudies />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/admin-consultant" element={<AdminConsultant />} />
            {process.env.NODE_ENV !== "production" && <Route path="/__scenes" element={<SceneGallery />} />}
          </Routes>
        </main>
        <Footer />
        <BackToTop />
        <AIConsultant />
      </BrowserRouter>
    </div>
  );
}

export default App;
