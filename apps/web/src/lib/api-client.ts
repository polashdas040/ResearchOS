const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const ACCESS_TOKEN_KEY = "researchos.access_token";
const REFRESH_TOKEN_KEY = "researchos.refresh_token";
let refreshPromise: Promise<string> | null = null;

type TokenResponse = {
  access_token: string;
  refresh_token: string;
};

type RegisterInput = {
  email: string;
  password: string;
  fullName: string;
  organizationName: string;
};

export type ProjectResponse = {
  id: string;
  name: string;
  description: string | null;
};

export type ProjectListResponse = {
  items: ProjectResponse[];
};

export type ConversationResponse = {
  id: string;
  project_id: string;
  title: string;
  messages?: MessageListResponse | null;
};

export type ConversationListResponse = {
  items: ConversationResponse[];
};

export type MessageResponse = {
  id: string;
  message_type: string;
  content: string;
};

export type FileResponse = {
  id: string;
  filename: string;
  content_type?: string;
  status: string;
};

export type FileListResponse = {
  items: FileResponse[];
  total: number;
};

export type FileReference = {
  number: number;
  file_id: string;
  filename: string;
  citation: string;
  evidence?: string;
  url?: string;
  source_type?: "file" | "literature";
  source_id?: string;
  pdf_url?: string;
};

export type FileReferenceListResponse = {
  items: FileReference[];
};

export type LiteratureReference = {
  number: number;
  source_id: string;
  title: string;
  citation: string;
  evidence: string;
  url?: string | null;
  pdf_url?: string | null;
};

export type LiteratureReferenceListResponse = {
  items: LiteratureReference[];
};

export type AttachedFile = FileResponse & {
  downloadUrl: string;
};

type MessageListResponse = {
  items: MessageResponse[];
};

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getStoredRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export async function register(input: RegisterInput): Promise<void> {
  await request("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      full_name: input.fullName,
      organization_name: input.organizationName
    })
  });
  await login(input.email, input.password);
}

export async function login(email: string, password: string): Promise<void> {
  const tokens = await request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  storeTokens(tokens);
}

export async function listProjects(): Promise<ProjectListResponse> {
  return authorizedRequest("/projects");
}

export async function createProject(name: string): Promise<ProjectResponse> {
  return authorizedRequest("/projects", {
    method: "POST",
    body: JSON.stringify({ name })
  });
}

export async function deleteProject(projectId: string): Promise<void> {
  await authorizedRequest(`/projects/${projectId}`, { method: "DELETE" });
}

export async function updateProject(
  projectId: string,
  input: { name?: string; description?: string }
): Promise<ProjectResponse> {
  return authorizedRequest(`/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(input)
  });
}

export async function listConversations(projectId: string): Promise<ConversationListResponse> {
  return authorizedRequest(`/projects/${projectId}/conversations`);
}

export async function createConversation(
  projectId: string,
  title: string
): Promise<ConversationResponse> {
  return authorizedRequest(`/projects/${projectId}/conversations`, {
    method: "POST",
    body: JSON.stringify({ title })
  });
}

export async function getConversation(conversationId: string): Promise<ConversationResponse> {
  return authorizedRequest(`/conversations/${conversationId}`);
}

export async function renameConversation(
  conversationId: string,
  title: string
): Promise<ConversationResponse> {
  return authorizedRequest(`/conversations/${conversationId}`, {
    method: "PATCH",
    body: JSON.stringify({ title })
  });
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await authorizedRequest(`/conversations/${conversationId}`, { method: "DELETE" });
}

export async function sendChatMessage(
  conversationId: string,
  content: string
): Promise<MessageResponse> {
  return authorizedRequest(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message_type: "USER", content })
  });
}

export async function uploadProjectFile(projectId: string, file: File): Promise<FileResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await authorizedFetch(`/projects/${projectId}/files`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }
  return (await response.json()) as FileResponse;
}

export async function listProjectFiles(projectId: string): Promise<FileListResponse> {
  return authorizedRequest(`/projects/${projectId}/files`);
}

export async function deleteProjectFile(fileId: string): Promise<void> {
  await authorizedRequest(`/files/${fileId}`, { method: "DELETE" });
}

export async function listProjectFileReferences(projectId: string): Promise<FileReferenceListResponse> {
  return authorizedRequest(`/projects/${projectId}/file-references`);
}

export async function searchLiteratureReferences(
  projectId: string,
  query: string,
  limit = 5
): Promise<LiteratureReferenceListResponse> {
  const parameters = new URLSearchParams({ query, limit: String(limit) });
  return authorizedRequest(`/projects/${projectId}/literature-references?${parameters}`);
}

export async function saveLiteratureReference(
  projectId: string,
  reference: LiteratureReference
): Promise<FileResponse> {
  return authorizedRequest(`/projects/${projectId}/literature-references/import`, {
    method: "POST",
    body: JSON.stringify({
      title: reference.title,
      citation: reference.citation,
      evidence: reference.evidence,
      url: reference.url ?? null,
      pdf_url: reference.pdf_url ?? null
    })
  });
}

export function fileDownloadUrl(fileId: string): string {
  return `${API_BASE_URL}/files/${fileId}/download`;
}

export async function openProjectFile(fileId: string): Promise<void> {
  const response = await authorizedFetch(`/files/${fileId}/download`);
  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }
  const blobUrl = window.URL.createObjectURL(await response.blob());
  window.open(blobUrl, "_blank", "noreferrer");
  window.URL.revokeObjectURL(blobUrl);
}

export async function streamChatMessage(
  conversationId: string,
  content: string,
  onDelta: (delta: string) => void,
  fileIds: string[] = [],
  options: {
    history?: Array<{ role: "user" | "assistant"; content: string }>;
    citationStyle?: "IEEE" | "APA 7" | "Harvard" | "MLA 9";
    referenceContext?: string;
    requireReferences?: boolean;
  } = {}
): Promise<void> {
  const response = await authorizedFetch(
    `/conversations/${conversationId}/messages/stream`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        content,
        file_ids: fileIds,
        history: options.history ?? [],
        citation_style: options.citationStyle ?? "IEEE",
        reference_context: options.referenceContext ?? "",
        require_references: options.requireReferences ?? false
      })
    }
  );

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }
  if (!response.body) {
    throw new Error("Streaming response was empty.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const eventText of events) {
      const event = parseServerSentEvent(eventText);
      if (event.name === "message.delta" && typeof event.data.delta === "string") {
        onDelta(event.data.delta);
      }
      if (event.name === "message.failed") {
        throw new Error(String(event.data.error ?? "Message failed."));
      }
    }
  }
}

function parseServerSentEvent(eventText: string): { name: string; data: Record<string, unknown> } {
  const eventLine = eventText.split("\n").find((line) => line.startsWith("event: "));
  const dataLine = eventText.split("\n").find((line) => line.startsWith("data: "));
  return {
    name: eventLine?.slice("event: ".length) ?? "",
    data: dataLine ? (JSON.parse(dataLine.slice("data: ".length)) as Record<string, unknown>) : {}
  };
}

function storeTokens(tokens: TokenResponse): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
}

async function authorizedRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await authorizedFetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });
  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function authorizedFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getStoredAccessToken();
  if (!token) {
    throw new Error("Please sign in first.");
  }
  const execute = (accessToken: string) => fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init.headers,
      Authorization: `Bearer ${accessToken}`
    }
  });
  let response = await execute(token);
  if (response.status !== 401) return response;
  response = await execute(await refreshAccessToken());
  return response;
}

async function refreshAccessToken(): Promise<string> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) {
      clearStoredTokens();
      throw new Error("Your session expired. Please sign in again.");
    }
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    if (!response.ok) {
      clearStoredTokens();
      throw new Error("Your session expired. Please sign in again.");
    }
    const tokens = (await response.json()) as TokenResponse;
    storeTokens(tokens);
    return tokens.access_token;
  })();
  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

function clearStoredTokens() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers
    }
  });

  if (!response.ok) {
    const message = await readErrorMessage(response);
    throw new Error(message);
  }

  return (await response.json()) as T;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as {
      detail?: string | Array<{ loc?: string[]; msg?: string }>;
    };
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => {
          const field = item.loc?.at(-1);
          return field && item.msg ? `${field}: ${item.msg}` : item.msg;
        })
        .filter(Boolean)
        .join("; ");
    }
    return "Request failed.";
  } catch {
    return "Request failed.";
  }
}
