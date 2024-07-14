(_ => {
  document.getElementsByTagName('textarea')[0].value += 'standard::' + performance.now() + '\n';
})()