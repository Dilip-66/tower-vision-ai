import type { Metadata } from "next";
import "./globals.css";
import { THEME_INIT_SCRIPT } from "@/lib/theme-script";

const DESCRIPTION =
  "AI-powered tower vision detection and visualization. Upload an image and let a YOLO-based computer vision model identify Monopole Tower and Supporting Tower structures, with bounding boxes, class labels, and confidence scores.";

export const metadata: Metadata = {
  title: "Tower Vision — AI-Powered Tower Detection & Visualization",
  description: DESCRIPTION,
  applicationName: "Tower Vision",
  metadataBase: new URL("https://forcanopy.com"),
  openGraph: {
    title: "Tower Vision — AI-Powered Tower Detection & Visualization",
    description: DESCRIPTION,
    url: "https://forcanopy.com",
    siteName: "Tower Vision",
    images: [{ url: "https://forcanopy.com/og-image.png", width: 1200, height: 675 }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tower Vision — AI-Powered Tower Detection & Visualization",
    description: DESCRIPTION,
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
    name: "Tower Vision",
    url: "https://forcanopy.com",
    description: DESCRIPTION,
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
