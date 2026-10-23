import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  createProject,
  deleteProject,
  getStoredAccessToken,
  listProjectFiles,
  listProjectFileReferences,
  login,
  register,
  searchLiteratureReferences,
  sendChatMessage,
  streamChatMessage,
  uploadProjectFile,
  openProjectFile
} from "./api-client";

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

it("stores tokens after login", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => tokenResponse()) as unknown as typeof fetch
  );

  await login("researcher@example.com", "password");

  expect(getStoredAccessToken()).toBe("access-token");
});

it("logs in automatically after registration", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(okResponse({ id: "user-1" }))
    .mockResolvedValueOnce(tokenResponse());
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  await register({
    email: "new@example.com",
    password: "password",
    fullName: "New User",
    organizationName: "Lab"
  });

  expect(fetchMock).toHaveBeenCalledTimes(2);
  expect(getStoredAccessToken()).toBe("access-token");
});

it("sends authorized project and chat requests", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(okResponse({ id: "project-1", name: "New project" }))
    .mockResolvedValueOnce(okResponse({ id: "message-1", content: "hello" }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  await createProject("New project");
  await sendChatMessage("conversation-1", "hello");

  expect(fetchMock).toHaveBeenNthCalledWith(
    1,
    "http://localhost:8000/projects",
    expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Bearer access-token" })
    })
  );
  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    "http://localhost:8000/conversations/conversation-1/messages",
    expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Bearer access-token" })
    })
  );
});

it("handles a successful project deletion with no response body", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204 } as Response);
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  await expect(deleteProject("project-1")).resolves.toBeUndefined();
  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/projects/project-1",
    expect.objectContaining({ method: "DELETE" })
  );
});

it("refreshes an expired access token and retries the authorized request", async () => {
  localStorage.setItem("researchos.access_token", "expired-token");
  localStorage.setItem("researchos.refresh_token", "refresh-token");
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce({ ok: false, status: 401 } as Response)
    .mockResolvedValueOnce(okResponse({
      access_token: "refreshed-access-token",
      refresh_token: "rotated-refresh-token"
    }))
    .mockResolvedValueOnce(okResponse({ id: "project-1", name: "Recovered project" }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  await createProject("Recovered project");

  expect(fetchMock).toHaveBeenNthCalledWith(
    2,
    "http://localhost:8000/auth/refresh",
    expect.objectContaining({ body: JSON.stringify({ refresh_token: "refresh-token" }) })
  );
  expect(fetchMock).toHaveBeenNthCalledWith(
    3,
    "http://localhost:8000/projects",
    expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Bearer refreshed-access-token" })
    })
  );
  expect(getStoredAccessToken()).toBe("refreshed-access-token");
  expect(localStorage.getItem("researchos.refresh_token")).toBe("rotated-refresh-token");
});

it("streams assistant deltas", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        encoder.encode('event: message.delta\ndata: {"delta":"Hi"}\n\n')
      );
      controller.enqueue(
        encoder.encode('event: message.delta\ndata: {"delta":" there"}\n\n')
      );
      controller.close();
    }
  });
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok: true, body: stream }) as Response) as unknown as typeof fetch
  );
  const deltas: string[] = [];

  await streamChatMessage("conversation-1", "hello", (delta) => deltas.push(delta), ["file-1"]);

  expect(deltas).toEqual(["Hi", " there"]);
  expect(fetch).toHaveBeenCalledWith(
    "http://localhost:8000/conversations/conversation-1/messages/stream",
    expect.objectContaining({
      body: JSON.stringify({
        content: "hello",
        file_ids: ["file-1"],
        history: [],
        citation_style: "IEEE",
        reference_context: "",
        require_references: false
      })
    })
  );
});

it("uploads project files with authorization", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi.fn(async () =>
    okResponse({ id: "file-1", filename: "notes.txt", status: "READY" })
  );
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  const file = new File(["hello"], "notes.txt", { type: "text/plain" });
  await uploadProjectFile("project-1", file);

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/projects/project-1/files",
    expect.objectContaining({
      method: "POST",
      headers: { Authorization: "Bearer access-token" },
      body: expect.any(FormData)
    })
  );
});

it("lists project files so document context survives a refresh", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi.fn(async () =>
    okResponse({ items: [{ id: "file-1", filename: "paper.pdf", status: "READY" }], total: 1 })
  );
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  const files = await listProjectFiles("project-1");

  expect(files.items[0].filename).toBe("paper.pdf");
  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/projects/project-1/files",
    expect.objectContaining({
      headers: expect.objectContaining({ Authorization: "Bearer access-token" })
    })
  );
});

it("loads IEEE source references for the document", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi.fn(async () => okResponse({
    items: [{ number: 1, file_id: "file-1", filename: "paper.pdf", citation: "[1] Paper" }]
  }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  const references = await listProjectFileReferences("project-1");

  expect(references.items[0].citation).toBe("[1] Paper");
  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/projects/project-1/file-references",
    expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer access-token" }) })
  );
});

it("searches external scholarly references for document generation", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const fetchMock = vi.fn(async () => okResponse({
    items: [{
      number: 1,
      source_id: "W1",
      title: "RAG Study",
      citation: '[1] A. Researcher, "RAG Study," Journal, 2025.',
      evidence: "RAG grounds generation in retrieved evidence."
    }]
  }));
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);

  const references = await searchLiteratureReferences("project-1", "RAG systems", 5);

  expect(references.items[0].title).toBe("RAG Study");
  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/projects/project-1/literature-references?query=RAG+systems&limit=5",
    expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer access-token" }) })
  );
});

it("opens project files with authorization instead of using an unauthenticated link", async () => {
  localStorage.setItem("researchos.access_token", "access-token");
  const response = {
    ok: true,
    blob: async () => new Blob(["pdf"], { type: "application/pdf" })
  } as Response;
  const fetchMock = vi.fn(async () => response);
  const openMock = vi.fn();
  const createObjectURLMock = vi.fn(() => "blob:http://localhost/file-1");
  const revokeObjectURLMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock as unknown as typeof fetch);
  vi.stubGlobal("open", openMock);
  vi.stubGlobal("URL", {
    createObjectURL: createObjectURLMock,
    revokeObjectURL: revokeObjectURLMock
  });

  await openProjectFile("file-1");

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/files/file-1/download",
    expect.objectContaining({
      headers: { Authorization: "Bearer access-token" }
    })
  );
  expect(openMock).toHaveBeenCalledWith("blob:http://localhost/file-1", "_blank", "noreferrer");
  expect(revokeObjectURLMock).toHaveBeenCalledWith("blob:http://localhost/file-1");
});

function tokenResponse(): Response {
  return okResponse({
    access_token: "access-token",
    refresh_token: "refresh-token",
    token_type: "bearer",
    expires_in: 900
  });
}

function okResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body
  } as Response;
}
