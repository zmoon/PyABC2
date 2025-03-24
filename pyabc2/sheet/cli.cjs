const { render } = require('./render');

// Take ABC string as stdin
// Take parameters as --key=value flags

// Parse command-line arguments for parameters
const params = {};
process.argv.slice(2).forEach(arg => {
    const match = arg.match(/^--([^=]+)=(.*)$/);
    if (match) {
        const key = match[1];
        const value = match[2];
        params[key] = value;
    }
});

// Read ABC string from stdin
let abc = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
    abc += chunk;
});
process.stdin.on('end', () => {
    // Render the ABC string to SVG
    const svg = render(abc, params);
    console.log(svg);
});
