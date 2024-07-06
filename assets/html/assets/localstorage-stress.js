(_ => {
  const LS = window.localStorage;
  LS.first = 1;
  window.addText("1");

  setTimeout(_ => {
    LS.second = 2;
    window.addText("2")
  }, 500);

  eval("LS.third = 3")
  window.addText("3")

  const pro = new Promise((resolve) => {
    setTimeout(_ => {
      resolve();
    }, 250)
  })
  pro.then(_ => {
    LS.fourth = 4;
    window.addText("4")
  })

  const iframeElm = document.createElement('iframe')
  iframeElm.src = 'about:blank'
  document.body.appendChild(iframeElm)
  iframeElm.contentWindow.eval("window.localStorage.fifth = '5'; window.addText('5');");
})()