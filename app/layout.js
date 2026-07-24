import "./styles.css";

export const metadata = {
  title: "UK Financial Complaints Intelligence | Portfolio",
  description:
    "An auditable Python and Tableau analytics project built from FCA firm-level complaints data.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
