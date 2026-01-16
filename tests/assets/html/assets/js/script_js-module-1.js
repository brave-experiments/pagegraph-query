export async function run(){
    document.getElementsByTagName('textarea')[0].value += 'module1::' + performance.now() + '\n';     
    import(`/assets/js/script_js-module-2.js`).then(module => {
        module.run();
    });
}
