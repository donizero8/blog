window.addEventListener('load', async () => {
  let passed = 0, failed = 0;
  const tick = () => new Promise(resolve => setTimeout(resolve, 0));
  function assert(value, message) { if (!value) throw new Error(message); }
  async function test(name, action) {
    const result = document.createElement('li');
    try { await action(); passed++; result.className = 'pass'; result.textContent = `PASS ${name}`; }
    catch (error) { failed++; result.className = 'fail'; result.textContent = `FAIL ${name}: ${error.message}`; }
    document.querySelector('#results').append(result);
  }
  const editors = [...document.querySelectorAll('[data-medium-editor]')];
  const template = document.querySelector('.empty-form');
  await test('Empty inline stays uninitialized', () => {
    assert(!template.querySelector('[data-editor-initialized]'), 'Template initialized');
  });
  // Match Django's clone-and-rename workflow; event listeners are not cloned.
  const clone = template.cloneNode(true);
  clone.classList.remove('empty-form');
  clone.querySelector('textarea').name = 'notes-1-body';
  template.before(clone);
  clone.dispatchEvent(new CustomEvent('formset:added', {bubbles:true}));
  await tick();
  const added = clone.querySelector('[data-medium-editor]');
  for (const [name, editor] of [['default', editors[0]], ['compact', editors[1]], ['added inline', added]]) {
    const canvas = editor.querySelector('.medium-canvas');
    const button = selector => editor.querySelector(selector);
    async function reset(html = '<p>Alpha beta</p>') {
      canvas.innerHTML = html;
      canvas.focus();
      const range = document.createRange();
      range.selectNodeContents(canvas.firstElementChild);
      const selection = window.getSelection();
      selection.removeAllRanges(); selection.addRange(range);
      document.dispatchEvent(new Event('selectionchange'));
      await tick();
    }
    function activate(selector) {
      const target = button(selector);
      // Focus leaves the editable area, as with keyboard toolbar activation.
      target.focus(); target.click();
    }
    for (const [selector, tag] of [
      ['[data-command="bold"]','strong,b'], ['[data-command="italic"]','em,i'],
      ['[data-command="insertUnorderedList"]','ul'], ['[data-value="blockquote"]','blockquote'],
      ['[data-block="h2"]','h2'], ['[data-block="h3"]','h3'], ['[data-code]','pre'],
    ]) {
      await test(`${name}: ${tag} toggles on/off and preserves text`, async () => {
        await reset(); activate(selector);
        assert(canvas.querySelector(tag), 'Format not applied');
        assert(button(selector).getAttribute('aria-pressed') === 'true', 'Active state missing');
        activate(selector);
        assert(!canvas.querySelector(tag), 'Format not removed');
        assert(canvas.textContent === 'Alpha beta', 'Text changed');
        assert(button(selector).getAttribute('aria-pressed') === 'false', 'Active state not cleared');
        assert(editor.querySelector('textarea').value.includes('Alpha beta'), 'Form not synchronized');
      });
    }
    await test(`${name}: paragraph converts heading without losing text`, async () => {
      await reset('<h2>Alpha beta</h2>'); activate('[data-block="p"]');
      assert(canvas.querySelector('p') && !canvas.querySelector('h2'), 'Not a paragraph');
      assert(canvas.textContent === 'Alpha beta', 'Text changed');
    });
    await test(`${name}: pointer click toggles bold exactly once`, async () => {
      await reset();
      const bold = button('[data-command="bold"]');
      for (const expected of [true, false]) {
        bold.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, cancelable:true}));
        bold.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
        bold.click();
        assert(Boolean(canvas.querySelector('b,strong')) === expected, 'Pointer toggle incorrect');
      }
    });
    await test(`${name}: empty editor accepts bold typing then toggles off`, async () => {
      await reset('<p><br></p>');
      activate('[data-command="bold"]');
      document.execCommand('insertText', false, 'Bold');
      assert(canvas.querySelector('b,strong')?.textContent === 'Bold', 'Typing not bold');
      activate('[data-command="bold"]');
      document.execCommand('insertText', false, ' plain');
      assert(canvas.querySelector('b,strong')?.textContent === 'Bold', 'Bold stayed enabled');
      assert(canvas.textContent === 'Bold plain', 'Typing lost');
    });
    await test(`${name}: emoji opens/closes via click`, async () => {
      await reset(); activate('[data-emoji-toggle]');
      assert(!button('[data-emoji-picker]').hidden, 'Picker not opened');
      assert(button('[data-emoji-toggle]').getAttribute('aria-expanded') === 'true', 'Expanded state missing');
      activate('[data-emoji-toggle]');
      assert(button('[data-emoji-picker]').hidden, 'Picker not closed');
    });
    await test(`${name}: emoji inserts into selected editor and Escape closes picker`, async () => {
      await reset(); activate('[data-emoji-toggle]');
      activate('[data-emoji="📚"]');
      assert(canvas.textContent === '📚', 'Emoji inserted in wrong selection');
      assert(button('[data-emoji-picker]').hidden, 'Picker remained open');
      activate('[data-emoji-toggle]');
      canvas.focus();
      canvas.dispatchEvent(new KeyboardEvent('keydown', {key:'Escape', bubbles:true}));
      assert(button('[data-emoji-picker]').hidden, 'Escape failed');
    });
    for (const kind of ['youtube', 'location', 'image']) {
      await test(`${name}: ${kind} dialog opens via click`, async () => {
        await reset(); activate(`[data-${kind}]`);
        const dialog = button(`[data-${kind}-dialog]`);
        try { assert(dialog.open, 'Dialog not opened'); }
        finally { if (dialog.open) dialog.close(); }
      });
    }
    await test(`${name}: link dialog creates, edits and removes selected link`, async () => {
      await reset();
      activate('[data-command="createLink"]');
      assert(button('[data-link-dialog]').open, 'Dialog not open');
      button('[data-link-url]').value = 'https://example.com/';
      button('[data-link-save]').click();
      assert(canvas.querySelector('a')?.textContent === 'Alpha beta', 'Link not inserted');
      activate('[data-command="createLink"]');
      button('[data-link-url]').value = 'https://example.com/edited';
      button('[data-link-save]').click();
      assert(canvas.querySelector('a')?.getAttribute('href') === 'https://example.com/edited', 'Link not edited');
      activate('[data-command="createLink"]');
      button('[data-link-remove]').click();
      assert(!canvas.querySelector('a') && canvas.textContent === 'Alpha beta', 'Link removal lost text');
    });
    await test(`${name}: link inserts at collapsed cursor and rejects unsafe URL`, async () => {
      await reset();
      window.getSelection().collapseToEnd();
      document.dispatchEvent(new Event('selectionchange'));
      activate('[data-command="createLink"]');
      button('[data-link-url]').value = 'javascript:alert(1)';
      button('[data-link-save]').click();
      assert(button('[data-link-dialog]').open && !canvas.querySelector('a'), 'Unsafe URL accepted');
      button('[data-link-url]').value = 'https://example.com/';
      button('[data-link-save]').click();
      assert(canvas.querySelector('a')?.textContent === 'https://example.com/', 'Collapsed link missing');
      assert(canvas.textContent === 'Alpha betahttps://example.com/', 'Existing text changed');
    });
    await test(`${name}: cancelling link preserves contents`, async () => {
      await reset(); activate('[data-command="createLink"]');
      button('[data-link-cancel]').click();
      assert(canvas.innerHTML === '<p>Alpha beta</p>', 'Cancel changed content');
    });
    await test(`${name}: paragraph clears malformed outer headings at a caret`, async () => {
      await reset();
      const outer = document.createElement('h3');
      const inner = document.createElement('h2');
      const p = document.createElement('p'); p.textContent = 'Legacy heading';
      inner.append(p); outer.append(inner); canvas.replaceChildren(outer);
      const range = document.createRange(); range.setStart(p.firstChild, 5); range.collapse(true);
      window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
      document.dispatchEvent(new Event('selectionchange'));
      activate('[data-block="p"]');
      assert(!canvas.querySelector('h2,h3'), 'Outer heading survived');
      assert(canvas.textContent === 'Legacy heading', 'Text lost');
      assert(button('[data-block="p"]').getAttribute('aria-pressed') === 'true', 'Paragraph inactive');
    });
    await test(`${name}: heading to paragraph inside list with collapsed cursor`, async () => {
      await reset('<ul><li><h2>List heading</h2></li></ul>');
      const range = document.createRange(); range.setStart(canvas.querySelector('h2').firstChild, 4); range.collapse(true);
      window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
      document.dispatchEvent(new Event('selectionchange'));
      activate('[data-block="p"]');
      assert(!canvas.querySelector('h2,h3') && canvas.querySelector('li'), 'List conversion failed');
      assert(canvas.textContent === 'List heading', 'List text changed');
    });
  }
  await test('Repeated formset events do not register duplicate toggles', async () => {
    clone.dispatchEvent(new CustomEvent('formset:added', {bubbles:true}));
    clone.dispatchEvent(new CustomEvent('formset:added', {bubbles:true}));
    const canvas = added.querySelector('.medium-canvas');
    canvas.innerHTML = '<p>Once</p>'; canvas.focus();
    const range = document.createRange(); range.selectNodeContents(canvas.firstChild);
    window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
    document.dispatchEvent(new Event('selectionchange'));
    added.querySelector('[data-command="bold"]').click();
    assert(canvas.querySelector('b,strong'), 'Handler skipped or toggled twice');
  });
  await test('Formatting one editor does not modify another', async () => {
    const before = editors[0].querySelector('.medium-canvas').innerHTML;
    const canvas = added.querySelector('.medium-canvas');
    canvas.focus();
    const range = document.createRange(); range.selectNodeContents(canvas);
    window.getSelection().removeAllRanges(); window.getSelection().addRange(range);
    document.dispatchEvent(new Event('selectionchange'));
    added.querySelector('[data-command="bold"]').click();
    assert(editors[0].querySelector('.medium-canvas').innerHTML === before, 'Other editor changed');
  });
  document.querySelector('#summary').textContent = `${passed} passed, ${failed} failed`;
  document.title = `${failed ? 'FAIL' : 'PASS'} — Editor toggles`;
});
