export interface InventoryItem {
  size: string;
  quantity: number;
}

export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_url: string;
  price: number;
  inventory?: InventoryItem[];
}

export interface ChatProduct {
  product_id: string;
  name: string;
  price: number;
  image_url: string;
  description: string;
}

export interface ChatResponse {
  message: string;
  products: ChatProduct[];
  show_on_page: boolean;
}

export interface StoredChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  products: ChatProduct[];
  created_at: string;
}
