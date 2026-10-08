import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return <div className="not-found"><span>404</span><h1>This page wandered off campus.</h1><Link className="button" to="/">Return home</Link></div>;
}
