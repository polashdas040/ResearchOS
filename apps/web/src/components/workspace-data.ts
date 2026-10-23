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
  attachments?: MessageAttachment[];
  hidden?: boolean;
};

export type MessageAttachment = {
  id: string;
  filename: string;
  contentType: string;
};

export type RunStep = {
  label: string;
  agent: string;
  status: "complete" | "running" | "waiting" | "queued" | "failed" | "cancelled";
  startedAt?: string;
  duration?: string;
  detail?: string;
};

export type ResearchRunState = {
  prompt: string;
  startedAt: string;
  elapsed: string;
  steps: RunStep[];
  sources: string[];
  toolsUsed: string[];
  cost: string;
  error?: string;
  artifacts: string[];
  canRetry: boolean;
  canCancel: boolean;
};

export const messages: ChatMessage[] = [];

export const researchRun: ResearchRunState = {
  prompt: "Waiting for a research prompt",
  startedAt: "-",
  elapsed: "0s",
  steps: [
    { label: "Intent extraction", agent: "Intent Agent", status: "waiting", detail: "Waiting for prompt" },
    { label: "Literature search", agent: "Literature Agent", status: "waiting" },
    { label: "Evidence mapping", agent: "Evidence Agent", status: "waiting" },
    { label: "Gap analysis", agent: "Gap Analysis Agent", status: "waiting" },
    { label: "Hypothesis generation", agent: "Hypothesis Agent", status: "waiting" },
    { label: "Feasibility review", agent: "Feasibility Agent", status: "waiting" },
    { label: "Scientific critique", agent: "Scientific Critic", status: "waiting" },
    { label: "Verification", agent: "Verification Agent", status: "waiting" }
  ],
  sources: [],
  toolsUsed: [],
  cost: "0 credits",
  artifacts: [],
  canRetry: false,
  canCancel: false
};
