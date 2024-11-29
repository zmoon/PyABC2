const ABCJS_URL = 'https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js';


function initialize({ model }) {
    // TODO: skip if already loaded?

    model.set("_active_music_ids", []);

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


function getRandomString() {
    // from a-z and 0-1
    return Math.random().toString(36).substring(2, 9);
}


function render({ model, el }) {
    console.log("render")

    let abc = () => model.get('abc');
    let active_music_ids = model.get("_active_music_ids");

    let container = el;
    container.classList.add('container');

    let head = document.createElement('div');

    // ABCJS render target
    let music = document.createElement('div');
    let music_id = 'music' + '-' + getRandomString();
    music.id = music_id;
    music.classList.add('music');
    active_music_ids.push(music_id);

    container.appendChild(head);
    container.appendChild(music);

    function on_change() {
        console.log(`render_abc ${music_id}`);

        // Is music empty?
        if (music.innerHTML !== '') {
            console.log(`music ${music_id} is not empty`);
            music.innerHTML = '';
        };

        head.innerHTML = `abcjs widget<br><code>${abc()}</code>`;

        // NOTE: doesn't work with `music_id` passed as target,
        // even though it should, still not sure why
        let tunes = ABCJS.renderAbc(music, abc());
        if (tunes.length === 0) {
            console.log(`no tunes rendered for ${music_id}`);
        };
    }

    // Initial render
    on_change();

    // Listen for changes
    model.on("change:abc", on_change);

    // Clean up
    return () => {
        console.log(`cleanup ${music_id}`);

        container.innerHTML = '';

        // Remove ID from active music IDs
        let i = active_music_ids.indexOf(music_id);
        if (i > -1) {
            active_music_ids.splice(i, 1);
        };

        // Remove callback
        model.off("change:abc", on_change);
    };
}

export default { initialize, render };
