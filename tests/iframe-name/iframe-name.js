window.onload = async () => {
  const f = frames[0];
  const d = v => v === f ? "the iframe's window" : v === null ? "null" : v === undefined ? "undefined" : "another window";
  const log = ["contentType: " + document.contentType, "frames[0].name: " + JSON.stringify(f.name)];
  for (const n of ["x", "y"]) log.push(`window.${n}: ${d(window[n])}`);
  for (const n of ["x", "y"]) {
    const a = document.createElementNS("http://www.w3.org/1999/xhtml", "a");
    a.target = n;
    a.href = "about:blank#" + n;
    document.body.append(a);
    a.click();
    await new Promise(r => setTimeout(r, 500));
    log.push(`<a target=${n}> navigates the iframe: ${f.location.hash === "#" + n}`);
  }
  for (const n of ["x", "y"]) log.push(`window.open("", "${n}"): ${d(window.open("", n))}`);
  document.getElementById("log").textContent = log.join("\n");
};
