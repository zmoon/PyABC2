const ABCJS_URL = 'https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js';
const ABCJS_LOGO_URL = 'https://raw.githubusercontent.com/paulrosen/abcjs/' +
                       'refs/heads/main/docs/.vuepress/public/img/abcjs_comp_extended_08.svg';


function initialize({ model }) {

    model.set("_active_music_ids", []);
    model.set("_first_load", null);

    return new Promise((resolve, reject) => {
        if (window.ABCJS) {
            model.set("_first_load", false);
            console.log('ABCJS already loaded');
            resolve();
            return;
        };

        model.set("_first_load", true);
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

    let staffWidth = () => model.get('staff_width');
    let scale = () => model.get('scale');

    let active_music_ids = model.get("_active_music_ids");
    let first_load = model.get("_first_load");
    console.log(`first_load ${first_load}`);

    let container = el;
    container.classList.add('container');

    if (first_load) {
        let logo = document.createElement('img');
        logo.src = ABCJS_LOGO_URL;
        logo.height = '24';
        container.appendChild(logo);
    }

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
        let tunes = ABCJS.renderAbc(
            music,
            abc(),
            {
                staffwidth: staffWidth(),
                scale: scale(),
            },
        );
        if (tunes.length === 0) {
            console.log(`no tunes rendered for ${music_id}`);
        };
    }

    // Initial render
    on_change();

    // Listen for changes
    // model.on("change:abc", on_change);
    // model.on("change:scale", on_change);
    model.on("change", on_change);  // any change?

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
