import { Link } from "react-router-dom";

export default function AboutPage() {
  return (
    <div className="about-page">
      <section className="about-hero">
        <div><span className="eyebrow light">Our story</span><h1>Campus pride,<br />made your way.</h1></div>
        <p>Campus Customs celebrates the many communities that make Yale distinctive—from residential college courtyards to studios, labs, fields, and family traditions.</p>
      </section>
      <section className="content-width story-grid">
        <div className="story-number">01</div>
        <div><span className="eyebrow">Rooted in New Haven</span><h2>More than a name on a sweatshirt.</h2></div>
        <div><p>What you wear can say where you found your people. Our collection brings together familiar Yale symbols with designs for the smaller communities that shape a campus experience.</p><p>Whether you are arriving for the first time, cheering from afar, or returning years later, we want it to be easy to find something that feels connected to your story.</p></div>
      </section>
      <section className="about-values">
        <div className="content-width"><h2>Built around community</h2><div className="value-grid"><article><h3>Specific by design</h3><p>Collections reach beyond the university name to recognize teams, schools, colleges, and families.</p></article><article><h3>Easy to explore</h3><p>Clear product information and helpful search make a broad catalogue feel approachable.</p></article><article><h3>Personal service</h3><p>Our developing shopping assistant will help every visitor navigate choices with confidence.</p></article></div><Link className="button" to="/products">Shop all products</Link></div>
      </section>
    </div>
  );
}
