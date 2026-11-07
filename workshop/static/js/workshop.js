(() => {
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('#sidebar');
  const collapse = document.querySelector('.sidebar-collapse');
  const desktopOpen = document.querySelector('.desktop-menu-open');
  const searchToggle = document.querySelector('.search-toggle');
  const searchPanel = document.querySelector('.nav-search-panel');
  const setMenu = open => {
    toggle?.setAttribute('aria-expanded', String(open));
    toggle?.setAttribute('aria-label', open ? 'Đóng menu bài học' : 'Mở menu bài học');
    document.body.classList.toggle('menu-open', open);
  };
  const setCollapsed = collapsed => {
    document.body.classList.toggle('sidebar-collapsed', collapsed);
    collapse?.setAttribute('aria-expanded', String(!collapsed));
    desktopOpen?.setAttribute('aria-expanded', String(!collapsed));
  };
  toggle?.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  collapse?.addEventListener('click', () => { setCollapsed(true); desktopOpen.focus(); });
  desktopOpen?.addEventListener('click', () => { setCollapsed(false); collapse.focus(); });
  searchToggle?.addEventListener('click', () => {
    const open = searchPanel.hidden;
    searchPanel.hidden = !open;
    searchToggle.setAttribute('aria-expanded', String(open));
    if (open) {
      setCollapsed(false);
      setMenu(true);
      document.querySelector('#lesson-search').focus();
    } else {
      const input = document.querySelector('#lesson-search');
      input.value = '';
      input.dispatchEvent(new Event('input'));
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && document.body.classList.contains('menu-open')) {
      setMenu(false);
      (matchMedia('(max-width:720px)').matches ? toggle : searchToggle).focus();
    }
  });
  document.querySelector('#body')?.addEventListener('click', () => setMenu(false));
  sidebar?.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });

  document.querySelectorAll('pre').forEach(pre => {
    const code = pre.querySelector('code');
    if (!code) return;
    const frame = document.createElement('div');
    frame.className = 'code-block';
    pre.before(frame);
    frame.append(pre);
    const lines = document.createElement('span');
    lines.className = 'code-lines';
    lines.setAttribute('aria-hidden', 'true');
    const lineCount = code.textContent.replace(/\n$/, '').split('\n').length;
    lines.textContent = Array.from({length: lineCount}, (_, index) => index + 1).join('\n');
    pre.prepend(lines);
    const button = document.createElement('button');
    button.className = 'copy-code';
    const copyIcon = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M11 2H2v9M5 5h9v9H5z"/></svg>';
    button.innerHTML = copyIcon;
    button.setAttribute('aria-label', 'Sao chép đoạn mã');
    button.title = 'Sao chép đoạn mã';
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m2 8 4 4 8-8"/></svg>';
        button.dataset.copied = 'true';
        button.setAttribute('aria-label', 'Đã sao chép');
      } catch {
        button.dataset.copied = 'false';
        button.setAttribute('aria-label', 'Không sao chép được. Hãy chọn và sao chép mã.');
      }
      setTimeout(() => {
        button.innerHTML = copyIcon;
        delete button.dataset.copied;
        button.setAttribute('aria-label', 'Sao chép đoạn mã');
      }, 2500);
    });
    frame.append(button);
  });
  document.querySelectorAll('#body-inner table').forEach(table => {
    const container = document.createElement('div');
    container.className = 'table-container';
    container.tabIndex = 0;
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', 'Bảng thông tin, có thể cuộn ngang');
    table.before(container);
    container.append(table);
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
