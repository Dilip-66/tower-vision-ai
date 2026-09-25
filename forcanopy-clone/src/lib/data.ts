export type DetectionStatus = "Detected" | "No Detection";

/**
 * The model only supports the two structural categories below — do not add
 * more without retraining.
 */
export const TOWER_CLASSES = ["Monopole Tower", "Supporting Tower"] as const;

export type Detected = {
  label: string;
  /** when true renders the "+N more" pill */
  more?: boolean;
};

export type DetectionCard = {
  id: string;
  /** image reference shown as the card title */
  title: string;
  /** source file name shown under the title */
  source: string;
  /** detected structural category */
  category: (typeof TOWER_CLASSES)[number];
  status: DetectionStatus;
  image: string;
  alt: string;
  /** only present on the featured hero card */
  confidence?: {
    percent: number;
    region: string;
    note: string;
  };
  detectedOn?: string;
  detected?: Detected[];
  footer: string;
};

export const FEATURED: DetectionCard = {
  id: "44ca0066-0c9f-44fc-8391-d48327feeda6",
  title: "Tower Image 01",
  source: "tower_001.jpg",
  category: "Monopole Tower",
  status: "Detected",
  image: "/img/opt/tower-01.png",
  alt: "Tower 1 placeholder — detection bounding box",
  confidence: {
    percent: 92,
    region: "Region 1 of 1",
    note: "Bounding box drawn",
  },
  detected: [],
  detectedOn: undefined,
  footer: "2 bounding boxes",
};

export const RECENT: DetectionCard[] = [
  {
    id: "384ba709-5a95-4747-9ac0-2094e5b3f451",
    title: "Tower Image 02",
    source: "tower_002.jpg",
    category: "Monopole Tower",
    status: "Detected",
    image: "/img/opt/tower-02.png",
    alt: "Tower 2 placeholder — detection bounding box",
    detectedOn: "Oct 27, 2026",
    detected: [
      { label: "Monopole Tower" },
      { label: "Bounding Box" },
      { label: "+ 1 more", more: true },
    ],
    footer: "3 bounding boxes",
  },
  {
    id: "d07e6ab3-9be6-44f0-9e7b-c9c65fc5cad1",
    title: "Tower Image 03",
    source: "tower_003.jpg",
    category: "Supporting Tower",
    status: "Detected",
    image: "/img/opt/tower-03.png",
    alt: "Tower 3 placeholder — detection bounding box",
    detected: [{ label: "Supporting Tower" }, { label: "Bounding Box" }],
    footer: "1 detection · 2 bounding boxes",
  },
  {
    id: "44133eaf-ccfa-4d4e-8579-c412ab50aeaf",
    title: "Tower Image 04",
    source: "tower_004.jpg",
    category: "Monopole Tower",
    status: "No Detection",
    image: "/img/opt/tower-04.png",
    alt: "Tower 4 placeholder — detection bounding box",
    detected: [],
    footer: "0 bounding boxes",
  },
  {
    id: "3b8643e5-b8fc-425f-88ae-82409c8104cd",
    title: "Tower Image 05",
    source: "tower_005.jpg",
    category: "Supporting Tower",
    status: "Detected",
    image: "/img/opt/tower-05.png",
    alt: "Tower 5 placeholder — detection bounding box",
    detected: [{ label: "Supporting Tower" }, { label: "Bounding Box" }],
    footer: "1 detection · 1 bounding box",
  },
  {
    id: "61fbdea9-e59b-41ee-935e-a1dd2c9dc3ad",
    title: "Tower Image 06",
    source: "tower_006.jpg",
    category: "Monopole Tower",
    status: "Detected",
    image: "/img/opt/tower-06.png",
    alt: "Tower 6 placeholder — detection bounding box",
    detected: [{ label: "Monopole Tower" }, { label: "Bounding Box" }],
    footer: "1 detection · 1 bounding box",
  },
  {
    id: "16ca2e0c-2a58-497d-ad91-5818d93f4553",
    title: "Tower Image 07",
    source: "tower_007.jpg",
    category: "Supporting Tower",
    status: "Detected",
    image: "/img/opt/tower-07.png",
    alt: "Tower 7 placeholder — detection bounding box",
    detected: [
      { label: "Supporting Tower" },
      { label: "Bounding Box" },
      { label: "+ 1 more", more: true },
    ],
    footer: "4 bounding boxes",
  },
  {
    id: "47ad9b45-0b6f-4f11-b8eb-51b428ed6d75",
    title: "Tower Image 08",
    source: "tower_008.jpg",
    category: "Monopole Tower",
    status: "Detected",
    image: "/img/opt/tower-08.png",
    alt: "Tower 8 placeholder — detection bounding box",
    detected: [{ label: "Monopole Tower" }, { label: "Bounding Box" }],
    footer: "2 bounding boxes",
  },
  {
    id: "40b5491f-ed54-4729-9b64-83fda2c34cd6",
    title: "Tower Image 09",
    source: "tower_009.jpg",
    category: "Supporting Tower",
    status: "Detected",
    image: "/img/opt/tower-09.png",
    alt: "Tower 9 placeholder — detection bounding box",
    detected: [{ label: "Supporting Tower" }, { label: "Bounding Box" }],
    footer: "2 bounding boxes",
  },
  {
    id: "845fb343-6e2e-4a8f-930c-6c785946b88a",
    title: "Tower Image 10",
    source: "tower_010.jpg",
    category: "Monopole Tower",
    status: "No Detection",
    image: "/img/opt/tower-10.png",
    alt: "Tower 10 placeholder — detection bounding box",
    detected: [],
    footer: "0 bounding boxes",
  },
];

export const CLASS_DESCRIPTIONS: Record<
  (typeof TOWER_CLASSES)[number],
  string
> = {
  "Monopole Tower": "A tower structure built around a primary vertical pole.",
  "Supporting Tower":
    "A tower structure identified by its primary tower body and supporting structural elements.",
};

export const STEPS = [
  {
    n: "01",
    title: "Upload",
    body: "Upload a tower image to the platform.",
  },
  {
    n: "02",
    title: "Analyze",
    body: "The YOLO-based model processes the image and searches for supported tower structures.",
  },
  {
    n: "03",
    title: "Detect",
    body: "Detected structures are classified as Monopole Tower or Supporting Tower.",
  },
  {
    n: "04",
    title: "Visualize",
    body: "View bounding boxes, class labels, and confidence scores directly on the image.",
  },
];
