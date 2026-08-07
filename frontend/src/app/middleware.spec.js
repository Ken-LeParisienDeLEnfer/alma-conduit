import fetchMock from "jest-fetch-mock";

import agent from "../agent";
import { login, logout, register } from "../features/auth/authSlice";
import { localStorageMiddleware } from "./middleware";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build a minimal Redux-style store mock so we can invoke the middleware. */
function invokeMiddleware(action) {
	const store = { getState: jest.fn(), dispatch: jest.fn() };
	const next = jest.fn();
	localStorageMiddleware(store)(next)(action);
	return { store, next };
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeAll(() => fetchMock.enableMocks());
beforeEach(() => {
	fetchMock.resetMocks();
	localStorage.clear();
	// Start each test with no token in the agent
	agent.setToken(undefined);
});
afterAll(() => fetchMock.disableMocks());

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("localStorageMiddleware", () => {
	const TOKEN = "header.payload.signature";

	it("saves JWT to localStorage and sets it on the agent when login succeeds", () => {
		const action = login.fulfilled({ token: TOKEN, user: {} }, "", {});
		invokeMiddleware(action);

		expect(localStorage.getItem("jwt")).toBe(TOKEN);
	});

	it("calls agent.setToken with the JWT when login succeeds", async () => {
		// After setToken the agent embeds it in outgoing requests; we can verify
		// this by checking that a subsequent fetch carries the Authorization header.
		const action = login.fulfilled({ token: TOKEN, user: {} }, "", {});
		invokeMiddleware(action);

		fetchMock.mockResponseOnce(JSON.stringify({ user: {} }));
		await agent.Auth.current();

		const sentHeaders = fetchMock.mock.calls[0][1].headers;
		expect(sentHeaders.get("Authorization")).toBe(`Token ${TOKEN}`);
	});

	it("saves JWT to localStorage and sets it on the agent when register succeeds", () => {
		const action = register.fulfilled({ token: TOKEN, user: {} }, "", {});
		invokeMiddleware(action);

		expect(localStorage.getItem("jwt")).toBe(TOKEN);
	});

	it("calls agent.setToken with the JWT when register succeeds", async () => {
		const action = register.fulfilled({ token: TOKEN, user: {} }, "", {});
		invokeMiddleware(action);

		fetchMock.mockResponseOnce(JSON.stringify({ user: {} }));
		await agent.Auth.current();

		const sentHeaders = fetchMock.mock.calls[0][1].headers;
		expect(sentHeaders.get("Authorization")).toBe(`Token ${TOKEN}`);
	});

	it("removes JWT from localStorage on logout", () => {
		localStorage.setItem("jwt", TOKEN);

		const action = logout();
		invokeMiddleware(action);

		expect(localStorage.getItem("jwt")).toBeNull();
	});

	it("clears the token from the agent on logout", async () => {
		agent.setToken(TOKEN);
		const action = logout();
		invokeMiddleware(action);

		fetchMock.mockResponseOnce(JSON.stringify({ user: {} }));
		await agent.Auth.current();

		const sentHeaders = fetchMock.mock.calls[0][1].headers;
		expect(sentHeaders.get("Authorization")).toBeNull();
	});

	it("passes every action through to next()", () => {
		const action = { type: "some/unrelated/action", payload: 42 };
		const { next } = invokeMiddleware(action);
		expect(next).toHaveBeenCalledWith(action);
	});
});
