import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./auth";
import { ChatResultsProvider } from "./chat-results";
import "./styles.css";
import "./auth.css";
import "./chat.css";
import "./chat-results.css";
import "./usability.css";
import "./design.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider><ChatResultsProvider><App /></ChatResultsProvider></AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
