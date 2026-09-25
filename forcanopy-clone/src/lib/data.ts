export type TestStatus =
  | "Active"
  | "Funded"
  | "Expired"
  | "Cancelled"
  | "Needs Verification";

export type Detected = {
  label: string;
  /** when true renders the "+N more" pill */
  more?: boolean;
};

export type TestCardData = {
  id: string;
  title: string;
  brand: string;
  panel: string;
  status: TestStatus;
  image: string;
  alt: string;
  /** campaign progress (active requests) */
  progress?: { percent: number; raised: string; goal: string; daysLeft: string };
  /** published results */
  resultDate?: string;
  detected?: Detected[];
  screenedNote?: string;
  footer: string;
};

export const FEATURED: TestCardData = {
  id: "44ca0066-0c9f-44fc-8391-d48327feeda6",
  title: "Nerds Halloween Strawberry Mini Boxes Candy",
  brand: "Nerds",
  panel: "Heavy Metals Panel",
  status: "Active",
  image: "/img/opt/nerds.webp",
  alt: "Nerds Halloween Strawberry Mini Boxes Candy",
  progress: {
    percent: 45,
    raised: "$125.00",
    goal: "$276.00",
    daysLeft: "14 days left",
  },
  detected: [],
  screenedNote: undefined,
  footer: "3 backers",
};

export const RECENT: TestCardData[] = [
  {
    id: "384ba709-5a95-4747-9ac0-2094e5b3f451",
    title: "Lay's Classic Potato Chips - 8oz: Gluten-Free, No Artificial Flavors",
    brand: "Lay's",
    panel: "Pesticide Screen",
    status: "Funded",
    image: "/img/opt/lays.webp",
    alt: "Lay's Classic Potato Chips - 8oz: Gluten-Free, No Artificial Flavors",
    detected: [],
    screenedNote: undefined,
    resultDate: "Oct 27, 2026",
    footer: "3 backers",
  },
  {
    id: "d07e6ab3-9be6-44f0-9e7b-c9c65fc5cad1",
    title: "Sabra Classic Hummus",
    brand: "Sabra",
    panel: "Glyphosate + AMPA",
    status: "Funded",
    image: "/img/opt/sabra-hummus.jpeg",
    alt: "Sabra Classic Hummus",
    detected: [{ label: "Glyphosate" }],
    screenedNote: "1 of 2 screened",
    footer: "1 of 2 screened · 6 backers",
  },
  {
    id: "44133eaf-ccfa-4d4e-8579-c412ab50aeaf",
    title: "Driscoll's Strawberries",
    brand: "Driscoll's",
    panel: "Pesticide Screen",
    status: "Funded",
    image: "/img/opt/driscolls.webp",
    alt: "Driscoll's Strawberries",
    detected: [
      { label: "Flutriafol" },
      { label: "Pyrimethanil" },
      { label: "Myclobutanil" },
      { label: "+ 1 more", more: true },
    ],
    screenedNote: "4 of 592 screened",
    footer: "4 of 592 screened · 12 backers",
  },
  {
    id: "3b8643e5-b8fc-425f-88ae-82409c8104cd",
    title: "Oatly Barista Edition Oatmilk",
    brand: "Oatly",
    panel: "Glyphosate + AMPA",
    status: "Funded",
    image: "/img/opt/oatly.webp",
    alt: "Oatly Barista Edition Oatmilk",
    detected: [],
    screenedNote: "0 of 2 screened",
    footer: "0 of 2 screened · 10 backers",
  },
  {
    id: "61fbdea9-e59b-41ee-935e-a1dd2c9dc3ad",
    title: "Organic Dried Mango Slices",
    brand: "Terrasoul Superfoods",
    panel: "Heavy Metals Panel",
    status: "Funded",
    image: "/img/opt/mango.png",
    alt: "Organic Dried Mango Slices",
    detected: [{ label: "Arsenic (As)" }],
    screenedNote: "1 of 4 screened",
    footer: "1 of 4 screened · 6 backers",
  },
  {
    id: "16ca2e0c-2a58-497d-ad91-5818d93f4553",
    title: "Heritage Flakes",
    brand: "Nature's Path",
    panel: "Glyphosate + AMPA",
    status: "Funded",
    image: "/img/opt/heritage-flakes.webp",
    alt: "Heritage Flakes",
    detected: [],
    screenedNote: "0 of 2 screened",
    footer: "0 of 2 screened",
  },
  {
    id: "47ad9b45-0b6f-4f11-b8eb-51b428ed6d75",
    title: "Organic Roasted Seaweed Snack",
    brand: "Kirkland Signature",
    panel: "Heavy Metals Panel",
    status: "Funded",
    image: "/img/opt/seaweed-kirkland.png",
    alt: "Organic Roasted Seaweed Snack",
    detected: [
      { label: "Arsenic (As)" },
      { label: "Cadmium (Cd)" },
      { label: "Lead (Pb)" },
    ],
    screenedNote: "3 of 4 screened",
    footer: "3 of 4 screened",
  },
  {
    id: "40b5491f-ed54-4729-9b64-83fda2c34cd6",
    title: "Organic Roasted Seaweed With Sea Salt",
    brand: "Trader Joe's",
    panel: "Heavy Metals Panel",
    status: "Funded",
    image: "/img/opt/seaweed-tj.png",
    alt: "Organic Roasted Seaweed With Sea Salt",
    detected: [
      { label: "Arsenic (As)" },
      { label: "Cadmium (Cd)" },
      { label: "Lead (Pb)" },
    ],
    screenedNote: "3 of 4 screened",
    footer: "3 of 4 screened",
  },
  {
    id: "845fb343-6e2e-4a8f-930c-6c785946b88a",
    title: "Roasted Seaweed Snacks (Teriyaki)",
    brand: "Gimme",
    panel: "Heavy Metals Panel",
    status: "Funded",
    image: "/img/opt/seaweed-teriyaki.png",
    alt: "Roasted Seaweed Snacks (Teriyaki)",
    detected: [
      { label: "Arsenic (As)" },
      { label: "Cadmium (Cd)" },
      { label: "Lead (Pb)" },
    ],
    screenedNote: "3 of 4 screened",
    footer: "3 of 4 screened",
  },
];

export const STEPS = [
  {
    n: "01",
    title: "Browse",
    body: "Find open test requests for products you already buy, or start one for a product nobody has tested yet.",
  },
  {
    n: "02",
    title: "Pledge",
    body: "Chip in any amount. You are only charged if the request reaches its funding goal before it expires.",
  },
  {
    n: "03",
    title: "Test",
    body: "We purchase the product off the shelf and send it to an accredited, independent third-party lab.",
  },
  {
    n: "04",
    title: "Results",
    body: "Full lab reports are published for everyone, with plain-language context on what the numbers mean.",
  },
];
