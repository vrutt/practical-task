import type { Metadata } from "next";

import "@/assets/css/global.css";

export const metadata: Metadata = {
  title: "User authentication",
  description: "Secure account demo",
};
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
