const ABCJS_URL = 'https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js';


function initialize({ model }) {
    // TODO: skip if already loaded?
    return new Promise((resolve, reject) => {
        let script = document.createElement('script');
        script.src = ABCJS_URL;
        script.onload = () => {
            console.log('ABCJS loaded');
            resolve();
        };
        script.onerror = () => {
            console.error('Failed to load ABCJS');
            reject();
        };
        document.head.appendChild(script);
    });
}


function render({ model, el }) {
    let abc = () => model.get('abc');

    let div = document.createElement('div');
    div.innerHTML = `ABC is cool`;
    div.id = 'container';
    el.appendChild(div);

    // ABCJS render target
    let music = document.createElement('div');
    music.id = 'music';
    div.appendChild(music);

    ABCJS.renderAbc('music', abc());
}

export default { initialize, render };
