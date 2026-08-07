import { render } from "@testing-library/react";
import { unstable_HistoryRouter as HistoryRouter } from "react-router-dom";
import { createMemoryHistory } from "history";
import { Provider } from "react-redux";

import { makeStore } from "../app/store";

export default function _render(
	ui,
	{ store = makeStore(), history = createMemoryHistory() } = {},
) {
	return render(ui, {
		wrapper: ({ children }) => (
			<Provider store={store}>
				<HistoryRouter
					history={history}
					future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
				>
					{children}
				</HistoryRouter>
			</Provider>
		),
	});
}
