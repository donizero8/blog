const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = readFileSync('blog/static/blog/admin/book.js', 'utf8');
for (const initial of ['reading', 'finished']) {
  let change;
  const status = {value:initial, addEventListener:(_, fn) => { change = fn; }};
  const progress = {value:'28'};
  const row = {style:{}, chapterValue:'3'};
  const section = {setAttribute(){}};
  vm.runInNewContext(source, {window:{location:{pathname:'/admin/blog/book/add/'}}, document:{
    readyState:'complete',
    getElementById:id => ({id_status:status, id_progress:progress}[id] || null),
    querySelector:selector => selector === 'fieldset.book-progress-section' ? section : null,
    querySelectorAll:() => [row],
  }});
  status.value = 'finished'; change();
  assert.equal(progress.value, '100');
  assert.equal(progress.readOnly, true);
  assert.equal(row.hidden, true);
  assert.equal(row.style.display, 'none');
  assert.equal(section.hidden, false);
  status.value = 'reading'; change();
  assert.equal(progress.readOnly, false);
  assert.equal(row.hidden, false);
  assert.equal(row.style.display, '');
  assert.equal(row.chapterValue, '3');
  status.value = 'want'; change();
  assert.equal(section.hidden, true);
}
console.log('PASS: Finished progress and chapter visibility, Reading restoration, Want visibility');
