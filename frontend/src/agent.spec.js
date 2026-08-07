/**
 * Tests for the agent HTTP client (src/agent.js).
 *
 * Critical concern: the Authorization header must be present on all requests
 * after setToken() is called, and absent before / after it is cleared.
 */

import fetchMock from "jest-fetch-mock";
import agent from "./agent";

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeAll(() => fetchMock.enableMocks());

beforeEach(() => {
	fetchMock.resetMocks();
	// Reset internal token state between tests
	agent.setToken(undefined);
});

afterAll(() => fetchMock.disableMocks());

// ---------------------------------------------------------------------------
// Helper: capture the Headers object sent by the last fetch call
// ---------------------------------------------------------------------------

function lastRequestHeaders() {
	return fetchMock.mock.calls[0][1].headers;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("agent – Authorization header", () => {
	it("does NOT send Authorization header before setToken is called", async () => {
		fetchMock.mockResponseOnce(JSON.stringify({ tags: [] }));
		await agent.Tags.getAll();

		expect(lastRequestHeaders().get("Authorization")).toBeNull();
	});

	it('sends "Token <jwt>" Authorization header after setToken is called', async () => {
		const jwt = "test.jwt.token";
		agent.setToken(jwt);

		fetchMock.mockResponseOnce(JSON.stringify({ user: {} }));
		await agent.Auth.current();

		expect(lastRequestHeaders().get("Authorization")).toBe(`Token ${jwt}`);
	});

	it("does NOT send Authorization header after setToken is cleared", async () => {
		agent.setToken("some.token");
		agent.setToken(undefined);

		fetchMock.mockResponseOnce(JSON.stringify({ tags: [] }));
		await agent.Tags.getAll();

		expect(lastRequestHeaders().get("Authorization")).toBeNull();
	});

	it("uses the most recent token when setToken is called multiple times", async () => {
		agent.setToken("first.token");
		agent.setToken("second.token");

		fetchMock.mockResponseOnce(JSON.stringify({ user: {} }));
		await agent.Auth.current();

		expect(lastRequestHeaders().get("Authorization")).toBe(
			"Token second.token",
		);
	});
});

describe("agent – error handling", () => {
	it("throws the response body when the server returns a non-OK status", async () => {
		const errorBody = { errors: { email: ["is already taken"] } };
		fetchMock.mockResponseOnce(JSON.stringify(errorBody), { status: 422 });

		await expect(
			agent.Auth.register("taken", "taken@example.com", "password123"),
		).rejects.toEqual(errorBody);
	});

	it("resolves with the response body on a successful request", async () => {
		const successBody = { tags: ["react", "testing"] };
		fetchMock.mockResponseOnce(JSON.stringify(successBody));

		const result = await agent.Tags.getAll();
		expect(result).toEqual(successBody);
	});
});
