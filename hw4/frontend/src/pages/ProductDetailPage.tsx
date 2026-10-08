import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProduct } from "../api";
import type { Product } from "../types";

export default function ProductDetailPage() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<Product>();
  const [error, setError] = useState("");
  const [selectedSize, setSelectedSize] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setSelectedSize("");
    getProduct(productId, controller.signal)
      .then(setProduct)
      .catch((reason: Error) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, [productId]);

  if (error) return <div className="content-width page-section status-box error">{error}. <Link to="/products">Return to products</Link></div>;
  if (!product) return <div className="content-width page-section status-box">Loading product…</div>;

  const inventory = product.inventory ?? [];
  const available = inventory.filter((item) => item.quantity > 0);
  const selectedInventory = inventory.find((item) => item.size === selectedSize);

  return (
    <div className="content-width product-detail-page">
      <Link className="back-link" to="/products">← Back to all products</Link>
      <div className="product-detail">
        <div className="detail-image"><img src={product.image_url} alt={product.name} /></div>
        <section className="detail-copy">
          <span className="eyebrow">{product.garment_type}</span>
          <h1>{product.name}</h1>
          <div className="detail-price">${product.price.toFixed(2)}</div>
          <p className="detail-description">{product.description}</p>
          {product.colors.length > 0 && <div className="detail-group"><h2>Colors</h2><p>{product.colors.join(", ")}</p></div>}
          <div className="detail-group">
            <h2>Available sizes</h2>
            {inventory.length === 0 ? (
              <p>Stock information is not currently available.</p>
            ) : available.length === 0 ? (
              <p className="out-of-stock">Currently out of stock.</p>
            ) : (
              <div className="size-list">
                {inventory.map((item) => (
                  <button type="button" className={`${item.quantity > 0 ? "" : "sold-out"} ${selectedSize === item.size ? "selected" : ""}`} key={item.size} title={`${item.quantity} in stock`} disabled={item.quantity === 0} aria-pressed={selectedSize === item.size} onClick={() => setSelectedSize(item.size)}>
                    {item.size}<small>{item.quantity > 0 ? `${item.quantity} left` : "out"}</small>
                  </button>
                ))}
              </div>
            )}
          </div>
          {selectedInventory && <p className="selection-note">Size {selectedInventory.size} selected · {selectedInventory.quantity} available</p>}
          <button className="button purchase-placeholder" disabled={!selectedSize}>{selectedSize ? "Add to bag — coming soon" : "Select an available size"}</button>
          <div className="shopping-assurances"><span>✓ Local catalogue data</span><span>✓ Live size availability</span><span>✓ Secure account access</span></div>
        </section>
      </div>
    </div>
  );
}
