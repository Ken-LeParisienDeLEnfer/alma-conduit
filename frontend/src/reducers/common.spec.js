/**
 * Tests for the appLoad thunk in common.js.
 *
 * appLoad runs once on every page load (inside App.js useEffect).
 * It is responsible for restoring the user session from a stored JWT.
 * A bug here means every returning user is treated as anonymous.
 */

import fetchMock from "jest-fetch-mock";

import agent from "../agent";
import { makeStore } from "../app/store";
import { appLoad } from "./common";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const MOCK_TOKEN = "header.payload.signature";

const MOCK_USER_RESPONSE = {
	user: {
		email: "alice@example.com",
		username: "alice",
		bio: "Test bio",
		image: "https://example.com/avatar.png",
		token: MOCK_TOKEN,
	},
};

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeAll(() => fetchMock.enableMocks());

beforeEach(() => {
	fetchMock.resetMocks();
	agent.setToken(undefined);
});

afterAll(() => fetchMock.disableMocks());

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("appLoad thunk", () => {
	it("sets appLoaded to true regardless of whether a token is present", () => {
		const store = makeStore();
		store.dispatch(appLoad(null));
		expect(store.getState().common.appLoaded).toBe(true);
	});

	it("calls agent.setToken with the stored JWT when a token is provided", async () => {
		fetchMock.mockResponseOnce(JSON.stringify(MOCK_USER_RESPONSE));
		const store = makeStore();
		await store.dispatch(appLoad(MOCK_TOKEN));

		// Verify the agent was configured: the next fetch must carry the header.
		fetchMock.mockResponseOnce(JSON.stringify({ tags: [] }));
		await agent.Tags.getAll();

		const sentHeaders = fetchMock.mock.calls[1][1].headers;
		expect(sentHeaders.get("Authorization")).toBe(`Token ${MOCK_TOKEN}`);
	});

	it("fetches the current user when a token is provided", async () => {
		fetchMock.mockResponseOnce(JSON.stringify(MOCK_USER_RESPONSE));
		const store = makeStore();
		await store.dispatch(appLoad(MOCK_TOKEN));

		const { user } = store.getState().auth;
		expect(user.email).toBe(MOCK_USER_RESPONSE.user.email);
		expect(user.username).toBe(MOCK_USER_RESPONSE.user.username);
	});

	it("does NOT fetch the current user when no token is provided", () => {
		const store = makeStore();
		store.dispatch(appLoad(null));

		// No HTTP calls should have been made
		expect(fetchMock.mock.calls).toHaveLength(0);
	});

	it("does NOT configure the agent when no token is provided", async () => {
		const store = makeStore();
		store.dispatch(appLoad(null));

		fetchMock.mockResponseOnce(JSON.stringify({ tags: [] }));
		await agent.Tags.getAll();

		const sentHeaders = fetchMock.mock.calls[0][1].headers;
		expect(sentHeaders.get("Authorization")).toBeNull();
	});
});
