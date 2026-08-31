import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  createProject,
  getStoredAccessToken,
  login,
  register,
  sendChatMessage,
  streamChatMessage
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

  await streamChatMessage("conversation-1", "hello", (delta) => deltas.push(delta));

  expect(deltas).toEqual(["Hi", " there"]);
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
