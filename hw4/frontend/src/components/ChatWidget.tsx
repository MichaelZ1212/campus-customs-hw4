import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ApiError, getChatHistory, sendChatMessage } from "../api";
import type { ChatProduct } from "../types";
import { useChatResults } from "../chat-results";
import { useAuth } from "../auth";

interface Message {
  role: "user" | "assistant";
  content: string;
  products?: ChatProduct[];
}

const welcome: Message = {
  role: "assistant",
  content: "Hi! I’m the Bulldog Assistant. What kind of Yale gear can I help you find?",
};

const sessionExpired: Message = {
  role: "assistant",
  content: "Your login session has expired, so I’ve signed you out. Log in again to keep your chat history, or keep chatting as a guest.",
};

function renderInline(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith("**") && part.endsWith("**") && part.length > 4 ? <strong key={index}>{part.slice(2, -2)}</strong> : part.replace(/\*\*/g, ""));
}

/** Renders the small subset of Markdown the assistant is allowed to use: bold text and "- " lists. */
function MessageText({ text }: { text: string }) {
  const blocks: Array<{ list: boolean; lines: string[] }> = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const item = line.match(/^(?:[-*•]|\d+[.)])\s+(.*)$/);
    const content = item ? item[1] : line;
    const last = blocks[blocks.length - 1];
    if (last && last.list === Boolean(item)) last.lines.push(content);
    else blocks.push({ list: Boolean(item), lines: [content] });
  }
  return <>{blocks.map((block, index) => block.list
    ? <ul key={index}>{block.lines.map((line, i) => <li key={i}>{renderInline(line)}</li>)}</ul>
    : block.lines.map((line, i) => <p key={`${index}-${i}`}>{renderInline(line)}</p>))}</>;
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<Message[]>([welcome]);
  const [sending, setSending] = useState(false);
  const expired = useRef(false);
  const { showResults } = useChatResults();
  const { user, token, signOut } = useAuth();
  const location = useLocation();

  const expireSession = () => { expired.current = true; signOut(); };

  useEffect(() => {
    if (!user || !token) {
      setMessages(expired.current ? [welcome, sessionExpired] : [welcome]);
      expired.current = false;
      return;
    }
    let active = true;
    getChatHistory(token)
      .then((history) => { if (active) setMessages([welcome, ...history.map(({ role, content, products }) => ({ role, content, products }))]); })
      .catch((reason: Error) => {
        if (!active) return;
        if (reason instanceof ApiError && reason.status === 401) expireSession();
        else setMessages([welcome, { role: "assistant", content: reason.message }]);
      });
    return () => { active = false; };
  }, [user, token]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || sending) return;
    const userMessage: Message = { role: "user", content: text };
    // The API accepts at most 20 history messages; older context is not needed.
    const previous = messages.filter((message) => message !== welcome && message !== sessionExpired)
      .slice(-20).map(({ role, content }) => ({ role, content }));
    setMessages((current) => [...current, userMessage]);
    setDraft(""); setSending(true);
    try {
      const productMatch = location.pathname.match(/^\/products\/([^/]+)$/);
      const response = await sendChatMessage(
        text,
        previous,
        { path: location.pathname, product_id: productMatch ? decodeURIComponent(productMatch[1]) : null },
        token,
      );
      setMessages((current) => [...current, { role: "assistant", content: response.message, products: response.products }]);
      if (response.show_on_page && response.products.length) showResults(text, response.products);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 401) { expireSession(); return; }
      setMessages((current) => [...current, { role: "assistant", content: reason instanceof Error ? reason.message : "I’m unavailable right now. Please try again." }]);
    } finally { setSending(false); }
  };

  return (
    <aside className={`chat-widget ${open ? "is-open" : ""}`} aria-label="Shopping assistant">
      {open && <section className="chat-panel">
        <header><div><strong>Bulldog Assistant</strong><span><i /> AI shopping help</span></div><button className="icon-button" onClick={() => setOpen(false)} aria-label="Close chat">×</button></header>
        <div className="chat-messages" aria-live="polite">
          {messages.map((message, index) => <div key={index} className={`${message.role}-message chat-message`}>
            {message.role === "assistant" ? <MessageText text={message.content} /> : <p>{message.content}</p>}
            {message.products?.map((product) => <Link className="chat-product" key={product.product_id} to={`/products/${encodeURIComponent(product.product_id)}`} onClick={() => setOpen(false)}>
              <img src={product.image_url} alt="" /><span><strong>{product.name}</strong><small>${product.price.toFixed(2)}</small></span>
            </Link>)}
          </div>)}
          {sending && <div className="assistant-message chat-message typing" aria-label="Assistant is responding">•••</div>}
        </div>
        <form onSubmit={submit}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Ask about our products…" aria-label="Message" maxLength={2000} disabled={sending} />
          <button type="submit" disabled={sending || !draft.trim()} aria-label="Send message">➤</button>
        </form>
      </section>}
      <button className="chat-toggle" onClick={() => setOpen(!open)} aria-expanded={open}><span aria-hidden="true">{open ? "×" : "✦"}</span><span className="sr-only">{open ? "Close" : "Open"} shopping assistant</span></button>
    </aside>
  );
}
