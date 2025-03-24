// Use abcjs to render an ABC string with nodejs

import ABCJS from 'abcjs';
import { JSDOM } from 'jsdom';

const dom = new JSDOM(`<!DOCTYPE html><html><body></body></html>`);

// We make `document` globally accessibly since abcjs uses it to create the SVG
global.document = dom.window.document;

const XMLSerializer = dom.window.XMLSerializer;

const div = document.createElement('div', { id: 'target' });
document.body.appendChild(div);

let abc = `
K: G
M: 6/8
BAG AGE | GED GBd | edB dgb | age dBA |
`

// Render
ABCJS.renderAbc(
    div,
    abc,
    {
        scale: 1.0,
        staffWidth: 500,
    },
)

// Extract the SVG from the div and save it to a file
const svg = new XMLSerializer().serializeToString(div.firstChild);
console.log(svg);
