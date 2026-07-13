// Client-side preview of the certificate ID naming structure. Mirrors the
// backend token expansion in `backend/certificate_id.py` for instant feedback
// while an admin edits the format. The backend remains the source of truth.
const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

const randomRun = (length) =>
  Array.from({ length: Math.max(1, length) }, () =>
    ALPHABET[Math.floor(Math.random() * ALPHABET.length)]
  ).join("");

export const previewCertificateId = (
  format,
  { sequence = 1, courseCode = "COURSE", date = new Date() } = {}
) => {
  if (!format) return "";
  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return format.replace(/\{(seq|year|month|day|random|course)(?::(\d+))?\}/g, (match, token, arg) => {
    switch (token) {
      case "seq":
        return String(sequence).padStart(arg ? parseInt(arg, 10) : 0, "0");
      case "year":
        return year;
      case "month":
        return month;
      case "day":
        return day;
      case "random":
        return randomRun(arg ? parseInt(arg, 10) : 4);
      case "course":
        return courseCode;
      default:
        return match;
    }
  });
};
