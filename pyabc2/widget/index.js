function render({ model, el }) {
    let div = document.createElement('div');
    div.innerHTML = `ABC is cool`;
    div.id = 'abcjs-container';
    el.appendChild(div);
}

export default { render };
