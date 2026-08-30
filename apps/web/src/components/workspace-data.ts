export type ProjectSummary = {
  id: string;
  name: string;
  status: string;
  focus: string;
  accentClass: string;
};

export type ConversationSummary = {
  id: string;
  title: string;
  updatedAt: string;
  active?: boolean;
};

export type ChatMessage = {
  id: string;
  author: "Researcher" | "ResearchOS";
  content: string;
  tone: "user" | "assistant" | "system";
};

export type RunStep = {
  label: string;
  status: "complete" | "running" | "queued";
};

export type ArtifactSummary = {
  title: string;
  artifactType: string;
  version: string;
};

export const projects: ProjectSummary[] = [
  {
    id: "demo",
    name: "ADNI Literature Review",
    status: "Active",
    focus: "Longitudinal MRI biomarkers",
    accentClass: "bg-emerald-500"
  },
  {
    id: "glioma",
    name: "Glioma Imaging Cohort",
    status: "Draft",
    focus: "Segmentation and survival signals",
    accentClass: "bg-sky-500"
  },
  {
    id: "transformers",
    name: "Transformer Survey",
    status: "Paused",
    focus: "Scientific model comparison",
    accentClass: "bg-amber-500"
  }
];

export const conversations: ConversationSummary[] = [
  { id: "run-1", title: "Active evidence synthesis", updatedAt: "Now", active: true },
  { id: "run-2", title: "Dataset quality questions", updatedAt: "Yesterday" },
  { id: "run-3", title: "Reviewer concerns", updatedAt: "Aug 22" }
];

export const messages: ChatMessage[] = [
  {
    id: "m1",
    author: "Researcher",
    content: "Map evidence for hippocampal atrophy biomarkers and flag weak claims.",
    tone: "user"
  },
  {
    id: "m2",
    author: "ResearchOS",
    content:
      "I found converging evidence across longitudinal MRI studies. Citation validation in progress before final claim wording.",
    tone: "assistant"
  },
  {
    id: "m3",
    author: "ResearchOS",
    content:
      "Current evidence supports descriptive biomarker trends, while causal language remains unsupported.",
    tone: "system"
  }
];

export const runSteps: RunStep[] = [
  { label: "Dataset analyzed", status: "complete" },
  { label: "43 papers retrieved", status: "complete" },
  { label: "17 papers selected", status: "complete" },
  { label: "6 research gaps", status: "complete" },
  { label: "Evaluating feasibility", status: "running" },
  { label: "Experiment design", status: "queued" },
  { label: "Verification", status: "queued" }
];

export const artifacts: ArtifactSummary[] = [
  { title: "Evidence Map", artifactType: "Claim graph", version: "v1" },
  { title: "Gap Matrix", artifactType: "Literature table", version: "v1" },
  { title: "Dataset Profile", artifactType: "Data report", version: "v1" },
  { title: "Hypothesis Set", artifactType: "Idea workspace", version: "v1" }
];
