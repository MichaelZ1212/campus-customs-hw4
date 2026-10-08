import { createContext, ReactNode, useContext, useState } from "react";
import type { ChatProduct } from "./types";

interface ChatResultsContextValue {
  query: string;
  products: ChatProduct[];
  showResults: (query: string, products: ChatProduct[]) => void;
  clearResults: () => void;
}

const ChatResultsContext = createContext<ChatResultsContextValue | undefined>(undefined);

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<ChatProduct[]>([]);
  const showResults = (nextQuery: string, nextProducts: ChatProduct[]) => { setQuery(nextQuery); setProducts(nextProducts); };
  const clearResults = () => { setQuery(""); setProducts([]); };
  return <ChatResultsContext.Provider value={{ query, products, showResults, clearResults }}>{children}</ChatResultsContext.Provider>;
}

export function useChatResults() {
  const value = useContext(ChatResultsContext);
  if (!value) throw new Error("useChatResults must be used inside ChatResultsProvider");
  return value;
}
