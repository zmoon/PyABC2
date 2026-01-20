// Use abcjs to render an ABC string with nodejs

import ABCJS from 'abcjs';
import { JSDOM } from 'jsdom';

/**
 * Render an ABC notation string to sheet music with abcjs, returning an SVG string.
 *
 * @param {string} abc - The ABC notation string to render.
 * @param {Object.<string, *>} [params] - Optional abcjs parameters
 * (https://paulrosen.github.io/abcjs/visual/render-abc-options.html).
 * @returns {string} SVG string.
 */
export function render(abc, params = {}) {
    const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`);

    // We make `document` globally accessible since abcjs uses it to create the SVG
    global.document = dom.window.document;

    const XMLSerializer = dom.window.XMLSerializer;

    const div = document.createElement('div', { id: 'target' });
    document.body.appendChild(div);

    // Render
    ABCJS.renderAbc(div, abc, params);

    // Extract the SVG from the div and save it to a file
    return new XMLSerializer().serializeToString(div.firstChild);
}
