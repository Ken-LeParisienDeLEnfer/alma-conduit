/**
 * Tests for the article body rendering pipeline.
 *
 * The Article component renders user-generated content via:
 *   dangerouslySetInnerHTML={{ __html: xss(snarkdown(article.body)) }}
 *
 * This is the only XSS boundary in the UI. These tests verify that the
 * sanitization is actually applied and that legitimate markdown still works.
 */

import snarkdown from "snarkdown";
import xss from "xss";

/** Mirrors the exact expression used inside the Article component. */
function renderBody(body) {
	return xss(snarkdown(body));
}

describe("Article body – XSS sanitization", () => {
	it("neutralizes <script> tags in article body (encodes them as HTML entities)", () => {
		const body = 'Hello <script>alert("xss")</script> world';
		const html = renderBody(body);

		// The xss library encodes angle brackets, preventing script execution.
		// The raw <script> tag must not appear as executable HTML.
		expect(html).not.toContain("<script>");
		expect(html).not.toContain("</script>");
		// The encoded form is safe – the browser will render it as visible text,
		// not execute it.
		expect(html).toContain("&lt;script&gt;");
	});

	it("strips inline event handlers (onerror) from img tags", () => {
		const body = '<img src="x" onerror="alert(1)">';
		const html = renderBody(body);

		expect(html).not.toContain("onerror");
	});

	it("strips javascript: href links", () => {
		const body = '<a href="javascript:alert(1)">click me</a>';
		const html = renderBody(body);

		expect(html).not.toContain("javascript:");
	});

	it("renders bold markdown correctly", () => {
		const body = "This is **bold** text";
		const html = renderBody(body);

		expect(html).toContain("<strong>bold</strong>");
	});

	it("renders italic markdown correctly", () => {
		const body = "This is _italic_ text";
		const html = renderBody(body);

		expect(html).toContain("<em>italic</em>");
	});

	it("renders plain text without modification", () => {
		const body = "Just a plain sentence.";
		const html = renderBody(body);

		expect(html).toContain("Just a plain sentence.");
	});

	it("allows safe anchor tags through", () => {
		const body = "[visit](https://example.com)";
		const html = renderBody(body);

		expect(html).toContain('href="https://example.com"');
	});
});
