const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const ACCESS_TOKEN_KEY = "researchos.access_token";
const REFRESH_TOKEN_KEY = "researchos.refresh_token";

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

type MessageListResponse = {
  items: MessageResponse[];
};

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
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

export async function sendChatMessage(
  conversationId: string,
  content: string
): Promise<MessageResponse> {
  return authorizedRequest(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message_type: "USER", content })
  });
}

export async function streamChatMessage(
  conversationId: string,
  content: string,
  onDelta: (delta: string) => void
): Promise<void> {
  const token = getStoredAccessToken();
  if (!token) {
    throw new Error("Please sign in first.");
  }

  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}/messages/stream`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ content })
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
  const token = getStoredAccessToken();
  if (!token) {
    throw new Error("Please sign in first.");
  }
  return request<T>(path, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...init.headers
    }
  });
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
