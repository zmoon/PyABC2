const ABCJS_URL = 'https://cdn.jsdelivr.net/npm/abcjs@6.4.4/dist/abcjs-basic-min.js';
const ABCJS_LOGO_URL = 'https://raw.githubusercontent.com/paulrosen/abcjs/' +
                       'refs/heads/main/docs/' +
                       '.vuepress/public/img/abcjs_comp_extended_08.svg';


function initialize({ model }) {

    model.set("_active_music_ids", []);
    model.set("_first_load", null);

    return new Promise((resolve, reject) => {
        if (window.ABCJS) {
            model.set("_first_load", false);
            console.log('abcjs already loaded');
            resolve();
            return;
        };

        model.set("_first_load", true);
        let script = document.createElement('script');
        script.src = ABCJS_URL;
        script.onload = () => {
            console.log('abcjs loaded');
            resolve();
        };
        script.onerror = () => {
            console.error('Failed to load abcjs');
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

    let foregroundColor = () => model.get('foreground');
    let hide = () => model.get('hide');
    let lineThickness = () => model.get('line_thickness_increase');
    let scale = () => model.get('scale');
    let showDebugBox = () => model.get('debug_box');
    let showDebugGrid = () => model.get('debug_grid');
    let showDebugInput = () => model.get('debug_input');
    let showLogo = () => model.get('logo');
    let staffwidth = () => model.get('staff_width');
    let visualTranspose = () => model.get('transpose');

    let active_music_ids = model.get("_active_music_ids");
    let first_load = model.get("_first_load");
    console.log(`first_load ${first_load}`);

    let container = el;
    container.classList.add('container');

    if ((first_load || showLogo()) && !hide()) {
        let logo = document.createElement('img');
        logo.src = ABCJS_LOGO_URL;
        logo.height = '24';
        logo.width = '228';
        logo.title = 'abcjs logo';
        container.appendChild(logo);
    }

    let head = document.createElement('div');

    // abcjs render target
    let music = document.createElement('div');
    let music_id = 'music' + '-' + getRandomString();
    music.id = music_id;
    music.classList.add('music');
    active_music_ids.push(music_id);

    if (!hide()) {
        container.appendChild(head);
        container.appendChild(music);
    }

    function on_change() {
        console.log(`render_abc ${music_id}`);

        // Is music empty?
        if (music.innerHTML !== '') {
            console.log(`music ${music_id} is not empty`);
            music.innerHTML = '';
        };

        if (showDebugInput() && !hide()) {
            head.innerHTML = `<code>${abc()}</code>`;
        } else {
            head.innerHTML = '';
        }
        if (showDebugBox() && !hide()) {
            music.classList.add('debug');
            container.classList.add('debug');
        } else {
            music.classList.remove('debug');
            container.classList.remove('debug');
        }

        // Visual debug settings
        let showDebug = [];
        if (showDebugBox()) {showDebug.push('box')};
        if (showDebugGrid()) {showDebug.push('grid')};

        // NOTE: doesn't work with `music_id` passed as target,
        // even though it should, still not sure why
        let tunes = ABCJS.renderAbc(
            music,
            abc(),
            {
                foregroundColor: foregroundColor(),
                lineThickness: lineThickness(),
                scale: scale(),
                showDebug: showDebug,
                staffwidth: staffwidth(),
                visualTranspose: visualTranspose(),
            },
        );
        if (tunes.length === 0) {
            console.log(`no tunes rendered for ${music_id}`);
        };

        // Get the SVGs that have been rendered
        console.log(`music ${music_id} has ${music.children.length} children`);
        let svg_arr = [];
        for (let child of music.children) {
            if (child.tagName.toLowerCase() !== 'svg') {continue};
            let svg_str = new XMLSerializer().serializeToString(child);
            svg_arr.push(svg_str);
        }
        model.set('svgs', svg_arr);
        model.save_changes();
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
