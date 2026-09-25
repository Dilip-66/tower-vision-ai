import type { Metadata } from "next";
import "./globals.css";
import { THEME_INIT_SCRIPT } from "@/lib/theme-script";

export const metadata: Metadata = {
  title: "Canopy — Crowdfunded Contaminant Testing",
  description:
    "Crowdfund independent contaminant testing for everyday products. Back test requests for food, cosmetics, clothing, and household cleaners.",
  applicationName: "Canopy",
  metadataBase: new URL("https://forcanopy.com"),
  openGraph: {
    title: "Canopy — Crowdfunded Contaminant Testing",
    description:
      "Crowdfund independent contaminant testing for everyday products. Back test requests for food, cosmetics, clothing, and household cleaners.",
    url: "https://forcanopy.com",
    siteName: "Canopy",
    images: [{ url: "https://forcanopy.com/og-image.png", width: 1200, height: 675 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Canopy — Crowdfunded Contaminant Testing",
    description:
      "Crowdfund independent contaminant testing for everyday products. Back test requests for food, cosmetics, clothing, and household cleaners.",
    images: ["https://forcanopy.com/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const schema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Canopy",
    url: "https://forcanopy.com",
    description:
      "Crowdfunded contaminant testing for everyday products.",
  };

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
