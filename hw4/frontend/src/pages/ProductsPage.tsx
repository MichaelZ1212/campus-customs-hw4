import { useEffect, useMemo, useState } from "react";
import { getProducts } from "../api";
import ProductCard from "../components/ProductCard";
import type { Product } from "../types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError("");
    getProducts(controller.signal)
      .then(setProducts)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [reloadKey]);

  const categories = useMemo(() =>
    [...new Set(products.map((product) => product.garment_type))].sort((a, b) => a.localeCompare(b)),
  [products]);

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase();
    return products.filter((product) => {
      const matchesCategory = category === "all" || product.garment_type === category;
      const matchesQuery = !term || [product.name, product.garment_type, product.description, ...product.colors, ...product.search_tags]
        .join(" ").toLowerCase().includes(term);
      return matchesCategory && matchesQuery;
    });
  }, [products, query, category]);

  const clearFilters = () => { setQuery(""); setCategory("all"); };

  return (
    <div className="content-width page-section">
      <header className="page-heading">
        <span className="eyebrow">The collection</span>
        <h1>Campus classics, made personal.</h1>
        <p>Explore gear for every school, sport, college, and Bulldog in your life.</p>
      </header>
      <div className="catalogue-toolbar">
        <div className="catalogue-controls"><label>
          <span>Search</span>
          <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search the collection" />
        </label><label><span>Category</span><select value={category} onChange={(e) => setCategory(e.target.value)}><option value="all">All categories</option>{categories.map((item) => <option key={item} value={item}>{item}</option>)}</select></label></div>
        <span>{filtered.length} {filtered.length === 1 ? "product" : "products"}</span>
      </div>
      {loading && <div className="product-grid" aria-label="Loading products">{[1,2,3,4,5,6].map((item) => <div className="product-skeleton" key={item}><div /><span /><span /></div>)}</div>}
      {error && <div className="status-box error"><strong>We couldn’t load the collection.</strong><p>{error}</p><button className="button" onClick={() => setReloadKey((value) => value + 1)}>Try again</button></div>}
      {!loading && !error && filtered.length === 0 && <div className="status-box"><strong>No matching products found.</strong><p>Try a broader keyword or choose another category.</p><button className="button" onClick={clearFilters}>Clear filters</button></div>}
      <div className="product-grid">
        {!loading && !error && filtered.map((product) => <ProductCard key={product.product_id} product={product} />)}
      </div>
    </div>
  );
}
