import { screen, waitFor } from "@testing-library/react";
import user from "@testing-library/user-event";
import { faker } from "@faker-js/faker";
import fetchMock from "jest-fetch-mock";
import { createMemoryHistory } from "history";

import agent from "../../agent";
import { makeStore } from "../../app/store";
import { Status } from "../../common/utils";
import render from "../../test/utils";
import SettingsScreen from "./SettingsScreen";

describe("<SettingsScreen />", () => {
	const successRootState = {
		/**
		 * @type {import('./authSlice').AuthState}
		 */
		auth: {
			status: Status.SUCCESS,
			token: '{"sub":"warren_boyd"}',
			user: {
				email: "warren.boyd@mailinator.com",
				username: "warren_boyd",
				bio: "Asperiores quos dolorem iure et.",
				image: "https://cdn.fakercloud.com/avatars/sprayaga_128.jpg",
			},
		},
	};

	beforeAll(() => {
		fetchMock.enableMocks();
	});

	beforeEach(() => {
		agent.setToken('{"sub":"warren_boyd"}');
		fetchMock.resetMocks();
	});

	afterAll(() => {
		fetchMock.disableMocks();
	});

	it("should render the settings form", async () => {
		const history = createMemoryHistory({ initialEntries: ["/settings"] });
		const store = makeStore(successRootState);

		render(<SettingsScreen />, { history, store });
		expect(screen.queryByRole("list")).not.toBeInTheDocument();

		screen.getByRole("button", { name: "Update Settings" });
		screen.getByRole("button", { name: "Or click here to logout." });
	});

	it("should submit the settings form", async () => {
		fetchMock.mockResponse(async (request) => {
			const { user } = await request.json();
			// Keep the request in-flight briefly so the loading state is observable.
			await new Promise((resolve) => setTimeout(resolve, 100));

			return JSON.stringify({
				user: {
					...user,
					token: `{"sub":"${user.username}"}`,
					password: undefined,
				},
			});
		});
		const history = createMemoryHistory({ initialEntries: ["/settings"] });
		const store = makeStore(successRootState);
		const data = {
			image: faker.image.avatar(),
			username: faker.internet.username().replaceAll(/\W/g, "_").toLowerCase(),
			bio: faker.hacker.phrase(),
			email: faker.internet.exampleEmail().toLowerCase(),
			password: faker.internet.password({ length: 9, memorable: true }),
		};

		render(<SettingsScreen />, { history, store });

		await user.type(
			screen.getByPlaceholderText("URL of profile picture"),
			data.image,
		);
		await user.type(screen.getByPlaceholderText("Username"), data.username);
		await user.type(
			screen.getByPlaceholderText("Short bio about you"),
			data.bio,
		);
		await user.type(screen.getByPlaceholderText("Email"), data.email);
		await user.type(screen.getByPlaceholderText("New Password"), data.password);

		await user.click(screen.getByRole("button", { name: /update settings/i }));

		expect(
			screen.getByRole("button", { name: /update settings/i }),
		).toBeDisabled();

		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /update settings/i }),
			).not.toBeDisabled();
		});

		expect(screen.queryByRole("list")).not.toBeInTheDocument();
	});

	it("should show the validation errors", async () => {
		fetchMock.mockResponse(
			() =>
				// Keep the request in-flight briefly so the loading state is observable.
				new Promise((resolve) =>
					setTimeout(
						() =>
							resolve({
								body: `{
        "errors": {
          "password": ["is too short (minimum is 8 characters)"]
        }
      }`,
								init: { status: 422 },
							}),
						100,
					),
				),
		);
		const history = createMemoryHistory({ initialEntries: ["/settings"] });
		const store = makeStore(successRootState);

		render(<SettingsScreen />, { history, store });

		await user.type(
			screen.getByPlaceholderText("New Password"),
			faker.internet.password({ length: 6, memorable: true }),
		);

		await user.click(screen.getByRole("button", { name: /update settings/i }));

		expect(
			screen.getByRole("button", { name: /update settings/i }),
		).toBeDisabled();

		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /update settings/i }),
			).not.toBeDisabled();
		});

		expect(screen.getByRole("list")).not.toBeEmptyDOMElement();
	});

	it("should close the session and redirect", async () => {
		const history = createMemoryHistory({ initialEntries: ["/settings"] });
		const store = makeStore(successRootState);

		render(<SettingsScreen />, { history, store });

		await user.click(
			screen.getByRole("button", { name: "Or click here to logout." }),
		);

		await waitFor(() => {
			expect(history.location.pathname).toBe("/");
		});
	});

	it("should redirect if is not authenticated", async () => {
		const history = createMemoryHistory({ initialEntries: ["/settings"] });

		render(<SettingsScreen />, { history });

		expect(
			screen.queryByRole("heading", { name: "Your Settings" }),
		).not.toBeInTheDocument();

		expect(history.location.pathname).toBe("/");
	});
});
