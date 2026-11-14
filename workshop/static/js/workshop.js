(() => {
  const english = document.documentElement.lang.startsWith("en");
  const translations = {"Đóng menu bài học": "Close lesson menu", "Mở menu bài học": "Open lesson menu", "Kích thước gốc": "Original size", "Đóng ảnh": "Close image", "Đóng ×": "Close ×", "Ảnh phóng to; cuộn để xem chi tiết": "Enlarged image; scroll to see details", "Bấm để phóng to ảnh": "Click to enlarge image", "Ảnh minh họa": "Illustration", "Vừa màn hình": "Fit to screen", "Sao chép đoạn mã": "Copy code", "Đã sao chép": "Copied", "Không sao chép được. Hãy chọn và sao chép mã.": "Copy failed. Select and copy the code.", "Bảng thông tin, có thể cuộn ngang": "Information table; scroll horizontally", "Đang tìm…": "Searching…", "Không tìm thấy bài phù hợp.": "No matching lessons.", "Chưa tải được tìm kiếm. Bạn có thể dùng mục lục bên dưới.": "Search could not load. Use the lesson menu below."};
  const t = value => english ? (translations[value] || value) : value;
  const toggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('#sidebar');
  const collapse = document.querySelector('.sidebar-collapse');
  const desktopOpen = document.querySelector('.desktop-menu-open');
  const searchToggle = document.querySelector('.search-toggle');
  const searchPanel = document.querySelector('.nav-search-panel');
  const setMenu = open => {
    toggle?.setAttribute('aria-expanded', String(open));
    toggle?.setAttribute('aria-label', open ? t("Đóng menu bài học") : t("Mở menu bài học"));
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

  // Keep screenshots and diagrams readable without leaving the current lesson.
  if (typeof HTMLDialogElement !== 'undefined') {
    const viewer = document.createElement('dialog');
    viewer.className = 'image-viewer';
    viewer.setAttribute('aria-labelledby', 'image-viewer-title');
    viewer.innerHTML = `<div class="image-viewer-header"><h2 id="image-viewer-title"></h2><div class="image-viewer-controls"><button type="button" class="image-size" aria-pressed="false">${t("Kích thước gốc")}</button><button type="button" class="image-close" aria-label="${t("Đóng ảnh")}">${t("Đóng ×")}</button></div></div><div class="image-viewer-body" tabindex="0" aria-label="${t("Ảnh phóng to; cuộn để xem chi tiết")}"><img alt=""></div><p class="image-viewer-caption"></p>`;
    document.body.append(viewer);
    const picture = viewer.querySelector('img');
    const title = viewer.querySelector('h2');
    const caption = viewer.querySelector('.image-viewer-caption');
    const size = viewer.querySelector('.image-size');
    let opener;
    document.querySelectorAll('#body-inner figure > a').forEach(link => {
      const original = link.querySelector('img');
      if (!original) return;
      link.setAttribute('aria-label', `${english ? "Enlarge image:" : "Phóng to ảnh:"} ${original.alt}`);
      link.title = t("Bấm để phóng to ảnh");
      link.addEventListener('click', event => {
        if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        opener = link;
        picture.src = original.currentSrc || original.src;
        picture.alt = original.alt;
        title.textContent = original.alt || t("Ảnh minh họa");
        caption.textContent = link.closest('figure').querySelector('figcaption')?.textContent || '';
        viewer.dataset.mode = 'fit';
        size.textContent = t("Kích thước gốc");
        size.setAttribute('aria-pressed', 'false');
        viewer.showModal();
      });
    });
    size.addEventListener('click', () => {
      const actual = viewer.dataset.mode !== 'actual';
      viewer.dataset.mode = actual ? 'actual' : 'fit';
      size.textContent = actual ? t("Vừa màn hình") : t("Kích thước gốc");
      size.setAttribute('aria-pressed', String(actual));
    });
    viewer.querySelector('.image-close').addEventListener('click', () => viewer.close());
    viewer.addEventListener('click', event => { if (event.target === viewer) viewer.close(); });
    viewer.addEventListener('close', () => { picture.removeAttribute('src'); opener?.focus(); });
  }

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
    button.setAttribute('aria-label', t("Sao chép đoạn mã"));
    button.title = t("Sao chép đoạn mã");
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m2 8 4 4 8-8"/></svg>';
        button.dataset.copied = 'true';
        button.setAttribute('aria-label', t("Đã sao chép"));
      } catch {
        button.dataset.copied = 'false';
        button.setAttribute('aria-label', t("Không sao chép được. Hãy chọn và sao chép mã."));
      }
      setTimeout(() => {
        button.innerHTML = copyIcon;
        delete button.dataset.copied;
        button.setAttribute('aria-label', t("Sao chép đoạn mã"));
      }, 2500);
    });
    frame.append(button);
  });
  document.querySelectorAll('#body-inner table').forEach(table => {
    const container = document.createElement('div');
    container.className = 'table-container';
    container.tabIndex = 0;
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', t("Bảng thông tin, có thể cuộn ngang"));
    table.before(container);
    container.append(table);
  });

  const input = document.querySelector('#lesson-search');
  const results = document.querySelector('#search-results');
  const status = document.querySelector('#search-status');
  const navigation = document.querySelector('#lesson-navigation');
  const normalize = value => value.toLocaleLowerCase(english ? 'en' : 'vi').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd');
  let indexPromise;
  let sequence = 0;
  input?.addEventListener('input', async () => {
    const current = ++sequence;
    const query = normalize(input.value.trim());
    results.replaceChildren();
    results.hidden = status.hidden = !query;
    navigation.hidden = Boolean(query);
    if (!query) return;
    status.textContent = t("Đang tìm…");
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
      status.textContent = matches.length ? `${matches.length} ${english ? "matching lessons" : "bài phù hợp"}` : t("Không tìm thấy bài phù hợp.");
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
      status.textContent = t("Chưa tải được tìm kiếm. Bạn có thể dùng mục lục bên dưới.");
      navigation.hidden = false;
    }
  });
})();
