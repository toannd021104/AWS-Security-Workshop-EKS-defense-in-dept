(() => {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('#sidebar');
  const setMenu = open => {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Đóng menu bài học' : 'Mở menu bài học');
    document.body.classList.toggle('menu-open', open);
  };
  toggle?.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('menu-open')) {
      setMenu(false);
      toggle.focus();
    }
  });
  document.querySelector('#body')?.addEventListener('click', () => setMenu(false));
  sidebar?.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });

  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const button = document.createElement('button');
    button.className = 'copy-code';
    button.textContent = 'Sao chép';
    button.setAttribute('aria-label', 'Sao chép đoạn mã');
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = 'Đã sao chép';
      } catch { button.textContent = 'Hãy chọn và sao chép mã'; }
      setTimeout(() => { button.textContent = 'Sao chép'; }, 2500);
    });
    pre.append(button);
  });

  const input = document.querySelector('#lesson-search');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  const navigation = document.querySelector('#lesson-navigation');
  const normalize = value => value.toLocaleLowerCase('vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  let indexPromise;
  let sequence = 0;
  input?.addEventListener('input', async () => {
    const current = ++sequence;
    const query = normalize(input.value.trim());
    results.replaceChildren();
    results.hidden = status.hidden = !query;
    navigation.hidden = Boolean(query);
    if (!query) return;
    status.textContent = 'Đang tìm…';
    try {
      indexPromise ??= fetch(document.body.dataset.searchIndex).then(response => {
        if (!response.ok) throw new Error('Search unavailable');
        return response.json();
      }).catch(error => { indexPromise = undefined; throw error; });
      const pages = await indexPromise;
      if (current !== sequence) return;
      const words = query.split(/\s+/);
      const matches = pages.filter(page => words.every(word => normalize(page.title + ' ' + page.content).includes(word)))
        .sort((a, b) => Number(normalize(b.title).includes(query)) - Number(normalize(a.title).includes(query)));
      status.textContent = matches.length ? `${matches.length} bài phù hợp` : 'Không tìm thấy bài phù hợp.';
      matches.forEach(page => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.href = page.uri;
        link.textContent = page.title;
        item.append(link);
        results.append(item);
      });
    } catch {
      if (current !== sequence) return;
      status.textContent = 'Chưa tải được tìm kiếm. Bạn có thể dùng mục lục bên dưới.';
      navigation.hidden = false;
    }
  });
})();
