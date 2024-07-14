(_ => {
  document.getElementsByTagName('textarea')[0].value += 'async::' + performance.now() + '\n';
})()