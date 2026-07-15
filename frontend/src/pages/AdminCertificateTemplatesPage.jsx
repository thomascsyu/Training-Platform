import { Navigate } from "react-router-dom";

/** @deprecated Use /admin/certificates?tab=templates — kept as a redirect for old links. */
export const AdminCertificateTemplatesPage = () => (
  <Navigate to="/admin/certificates?tab=templates" replace />
);
