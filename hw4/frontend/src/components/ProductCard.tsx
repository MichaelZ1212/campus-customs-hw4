import { Link } from "react-router-dom";
import type { ChatProduct, Product } from "../types";

export default function ProductCard({ product }: { product: Product | ChatProduct }) {
  return (
    <Link className="product-card" to={`/products/${encodeURIComponent(product.product_id)}`}>
      <div className="product-image-wrap">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="product-badge">Campus pick</span>
        <span className="view-product">View details</span>
      </div>
      <div className="product-card-body">
        <span className="eyebrow">{"garment_type" in product ? product.garment_type : "Assistant match"}</span>
        <h2>{product.name}</h2>
        <p>{product.description}</p>
        <div className="card-footer"><strong className="price">${product.price.toFixed(2)}</strong><span aria-hidden="true">→</span></div>
      </div>
    </Link>
  );
}
