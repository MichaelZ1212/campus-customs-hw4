import { useEffect, useRef } from "react";
import ProductCard from "./ProductCard";
import { useChatResults } from "../chat-results";

export default function ChatResultsSection() {
  const { query, products, clearResults } = useChatResults();
  const section = useRef<HTMLElement>(null);
  useEffect(() => { if (products.length) section.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }, [products]);
  if (!products.length) return null;
  return <section ref={section} className="chat-results-section content-width" aria-live="polite">
    <header><div><span className="eyebrow">Selected by the Bulldog Assistant</span><h2>Matches for “{query}”</h2></div><button onClick={clearResults}>Clear results</button></header>
    <div className="product-grid">{products.map((product) => <ProductCard key={product.product_id} product={product} />)}</div>
  </section>;
}
