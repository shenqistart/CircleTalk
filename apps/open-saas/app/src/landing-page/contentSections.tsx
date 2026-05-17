import type { GridFeature } from "./components/FeaturesGrid";

export const features: GridFeature[] = [
  {
    name: "Private sessions",
    description: "Each Circle belongs to the signed-in user who created it.",
    emoji: "🔒",
    size: "small",
  },
  {
    name: "Google login",
    description: "Start from a familiar provider and keep access scoped.",
    emoji: "🔑",
    size: "small",
  },
  {
    name: "Persona debate",
    description: "Invite several perspectives into one structured discussion.",
    emoji: "🧭",
    size: "medium",
  },
  {
    name: "Credit settlement",
    description: "Reserve usage when discussion starts and settle on completion.",
    emoji: "💳",
    size: "large",
  },
  {
    name: "Decision artifacts",
    description: "Turn the transcript into a memo, recommendation, reasons, and debate map.",
    emoji: "📄",
    size: "large",
  },
  {
    name: "Follow-up questions",
    description: "Continue a completed Circle without starting from scratch.",
    emoji: "💬",
    size: "small",
  },
  {
    name: "Session history",
    description: "Restore prior Circle discussions from your account.",
    emoji: "🗂️",
    size: "small",
  },
  {
    name: "Worker streaming",
    description: "Watch the roundtable unfold as the worker sends events.",
    emoji: "🤖",
    size: "medium",
  },
  {
    name: "Built for launch",
    description: "Authentication, billing, and the core Circle workflow are connected.",
    emoji: "🚀",
    size: "medium",
  },
];

export const faqs = [
  {
    id: 1,
    question: "When are credits charged?",
    answer:
      "A discussion reserves usage when it starts and deducts credits after the Circle completes.",
  },
  {
    id: 2,
    question: "Can users see each other's Circles?",
    answer:
      "No. Circle sessions are scoped to the signed-in account that created them.",
  },
  {
    id: 3,
    question: "Which login provider is enabled?",
    answer:
      "The first external provider is Google, keeping signup simple while the product is still focused.",
  },
];

export const footerNavigation = {
  app: [
    { name: "Roundtable", href: "/roundtable" },
    { name: "Pricing", href: "/pricing" },
  ],
  company: [
    { name: "Privacy", href: "#" },
    { name: "Terms of Service", href: "#" },
  ],
};
