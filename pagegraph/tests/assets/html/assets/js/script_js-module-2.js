export async function run(){
    document.getElementsByTagName('textarea')[0].value += 'module2::' + performance.now() + '\n';     
}
