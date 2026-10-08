import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <span className="eyebrow light">New Haven · Connecticut</span>
          <h1>Wear your Yale story.</h1>
          <p>Thoughtfully selected gear for the classes, colleges, teams, and people that make campus feel like home.</p>
          <div className="hero-actions">
            <Link className="button button-light" to="/products">Shop the collection</Link>
            <Link className="text-link light" to="/about">Our story <span>→</span></Link>
          </div>
        </div>
        <div className="hero-art hero-collage" aria-hidden="true">
          <img className="hero-photo hero-photo-main" src="/product-images/basic-hoodie-big-yale.jpg" alt="" />
          <img className="hero-photo hero-photo-top" src="/product-images/boola-boola-t-shirt.jpg" alt="" />
          <div className="hero-seal"><span>Y</span><small>NEW HAVEN</small></div>
        </div>
      </section>

      <section className="values-section content-width">
        <div>
          <span className="eyebrow">Campus essentials</span>
          <h2>Belonging looks good on you.</h2>
        </div>
        <div className="value-grid">
          <article><span>01</span><h3>Your Yale</h3><p>Find designs for residential colleges, professional schools, athletics, and proud Bulldog families.</p></article>
          <article><span>02</span><h3>Made to remember</h3><p>Every sweatshirt and tee can carry a class, team, place, or moment worth keeping close.</p></article>
          <article><span>03</span><h3>Here to help</h3><p>Browse the full collection now, with a conversational shopping assistant joining the team soon.</p></article>
        </div>
      </section>

      <section className="cta-band">
        <p>From move-in day to reunion weekend</p>
        <h2>Find the piece that feels like yours.</h2>
        <Link className="button button-light" to="/products">Explore products</Link>
      </section>
    </>
  );
}
