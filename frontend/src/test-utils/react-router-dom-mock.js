import React from "react";

export const Navigate = () => null;
export const MemoryRouter = ({ children }) => children;
export const BrowserRouter = ({ children }) => children;
export const Routes = ({ children }) => children;
export const Route = () => null;
export const Link = ({ children, to }) => <a href={to}>{children}</a>;
export const useNavigate = () => jest.fn();
export const useParams = () => ({});
export const useSearchParams = () => [new URLSearchParams(), jest.fn()];
export const useLocation = () => ({ pathname: "/" });
