import { screen, waitFor } from "@testing-library/react";
import user from "@testing-library/user-event";
import { faker } from "@faker-js/faker";
import { createMemoryHistory } from "history";
import fetchMock from "jest-fetch-mock";
import { Route, Routes } from "react-router-dom";

import render from "../../test/utils";
import AuthScreen from "./AuthScreen";

describe("<AuthScreen />", () => {
	beforeAll(() => {
		fetchMock.enableMocks();
	});

	beforeEach(() => {
		fetchMock.resetMocks();
	});

	afterAll(() => {
		fetchMock.disableMocks();
	});

	it("should render the login form", async () => {
		const history = createMemoryHistory({
			initialEntries: ["/login"],
		});

		render(
			<Routes>
				<Route path="/login" element={<AuthScreen />} />
			</Routes>,
			{ history },
		);

		expect(screen.getByText(/need an account\?/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /sign in/i }),
		).toBeInTheDocument();
	});

	it("should submit the login form", async () => {
		fetchMock.mockResponse(
			() =>
				new Promise((resolve) => {
					setTimeout(() => {
						resolve(
							JSON.stringify({
								user: {
									email: "warren.boyd@mailinator.com",
									username: "warren_boyd",
									token: '{"sub":"warren_boyd"}',
									bio: "Asperiores quos dolorem iure et.",
									image: "https://cdn.fakercloud.com/avatars/sprayaga_128.jpg",
								},
							}),
						);
					}, Math.random() * 100);
				}),
		);
		const history = createMemoryHistory({
			initialEntries: ["/login"],
		});
		const data = {
			email: "warren.boyd@mailinator.com",
			password: "Pa$$w0rd!",
		};

		render(
			<Routes>
				<Route path="/login" element={<AuthScreen />} />
				<Route path="/" element={<div />} />
			</Routes>,
			{ history },
		);

		await user.type(screen.getByPlaceholderText("Email"), data.email);
		await user.type(screen.getByPlaceholderText("Password"), data.password);

		await user.click(screen.getByRole("button", { name: /sign in/i }));

		expect(screen.getByRole("button", { name: /sign in/i })).toBeDisabled();

		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /sign in/i }),
			).not.toBeDisabled();
		});

		expect(screen.queryByRole("list")).not.toBeInTheDocument();
	});

	it("should render the register form", async () => {
		const history = createMemoryHistory({
			initialEntries: ["/register"],
		});

		render(
			<Routes>
				<Route path="/register" element={<AuthScreen isRegisterScreen />} />
			</Routes>,
			{ history },
		);

		expect(screen.getByText(/have an account\?/i)).toBeInTheDocument();
		expect(
			screen.getByRole("button", { name: /sign up/i }),
		).toBeInTheDocument();
	});

	it("should submit the register form", async () => {
		fetchMock.mockResponse(async (request) => {
			const { user } = await request.json();
			// Keep the request in-flight briefly so the loading state is observable.
			await new Promise((resolve) => setTimeout(resolve, 100));

			return JSON.stringify({
				user: {
					email: user.email,
					username: user.username,
					token: `{"sub":"${user.username}"}`,
					bio: null,
					image: null,
				},
			});
		});
		const history = createMemoryHistory({
			initialEntries: ["/register"],
		});
		const data = {
			username: faker.internet
				.username()
				.replaceAll(/\W/g, "_")
				.toLowerCase()
				.substr(0, 20),
			email: faker.internet.email().toLowerCase(),
			password: faker.internet.password({ length: 12 }),
		};

		render(
			<Routes>
				<Route path="/register" element={<AuthScreen isRegisterScreen />} />
				<Route path="/login" element={<div />} />
			</Routes>,
			{
				history,
			},
		);

		await user.type(screen.getByPlaceholderText("Username"), data.username);
		await user.type(screen.getByPlaceholderText("Email"), data.email);
		await user.type(screen.getByPlaceholderText("Password"), data.password);

		await user.click(screen.getByRole("button", { name: /sign up/i }));

		expect(screen.getByRole("button", { name: /sign up/i })).toBeDisabled();

		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /sign up/i }),
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
								body: JSON.stringify({
									errors: {
										email: ["is invalid"],
										password: ["is too short (minimum is 8 characters)"],
										username: ["is too long (maximum is 20 characters)"],
									},
								}),
								init: { status: 422 },
							}),
						100,
					),
				),
		);
		const history = createMemoryHistory({
			initialEntries: ["/register"],
		});
		const data = {
			username: faker.lorem.sentences().replaceAll(/\W/g, "_").toLowerCase(),
			email: faker.internet.username().toLowerCase(),
			password: faker.internet.password({ length: 5 }),
		};

		render(
			<Routes>
				<Route path="/register" element={<AuthScreen isRegisterScreen />} />
			</Routes>,
			{
				history,
			},
		);

		await user.type(screen.getByPlaceholderText("Username"), data.username);
		await user.type(screen.getByPlaceholderText("Email"), data.email);
		await user.type(screen.getByPlaceholderText("Password"), data.password);

		await user.click(screen.getByRole("button", { name: /sign up/i }));

		expect(screen.getByRole("button", { name: /sign up/i })).toBeDisabled();

		await waitFor(() => {
			expect(
				screen.getByRole("button", { name: /sign up/i }),
			).not.toBeDisabled();
		});

		expect(screen.getByRole("list")).not.toBeEmptyDOMElement();
	});
});
