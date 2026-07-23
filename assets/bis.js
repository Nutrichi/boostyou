/* Boostyou.ai — BiS list browser (content/bis.html).

   Lists live as JSON files in content/bis-data/, one file per list:
     bis-data/<expansion>-<phase>-<class>-<spec>.json
   e.g. bis-data/wotlk-p4-druid-restoration.json
   Phase "preraid" is the per-expansion pre-raid list.
   A missing file simply shows the "coming soon" state — add the JSON
   and the list is live. See wotlk-p4-druid-restoration.json for the
   format (slots with 1-3 ranked items + source, enchants, gems).

   Deep links: bis.html#wotlk/p4/druid/restoration */

(function () {
  var DATA_BASE = 'bis-data/';

  var EXPANSIONS = [
    {
      id: 'classic', label: 'Classic', order: 0,
      phases: [
        { id: 'preraid', label: 'Pre-Raid' },
        { id: 'p1', label: 'P1 · Molten Core & Onyxia' },
        { id: 'p2', label: 'P2 · Dire Maul' },
        { id: 'p3', label: 'P3 · Blackwing Lair' },
        { id: 'p4', label: 'P4 · Zul’Gurub' },
        { id: 'p5', label: 'P5 · Ahn’Qiraj' },
        { id: 'p6', label: 'P6 · Naxxramas' }
      ]
    },
    {
      id: 'tbc', label: 'TBC', order: 1,
      phases: [
        { id: 'preraid', label: 'Pre-Raid' },
        { id: 'p1', label: 'P1 · Karazhan, Gruul & Mag' },
        { id: 'p2', label: 'P2 · SSC & Tempest Keep' },
        { id: 'p3', label: 'P3 · Hyjal & Black Temple' },
        { id: 'p4', label: 'P4 · Zul’Aman' },
        { id: 'p5', label: 'P5 · Sunwell Plateau' }
      ]
    },
    {
      id: 'wotlk', label: 'WotLK', order: 2,
      phases: [
        { id: 'preraid', label: 'Pre-Raid' },
        { id: 'p1', label: 'P1 · Naxx, OS & EoE' },
        { id: 'p2', label: 'P2 · Ulduar' },
        { id: 'p3', label: 'P3 · Trial of the Crusader' },
        { id: 'p4', label: 'P4 · ICC & Ruby Sanctum' }
      ]
    },
    {
      id: 'cata', label: 'Cataclysm', order: 3,
      phases: [
        { id: 'preraid', label: 'Pre-Raid' },
        { id: 'p1', label: 'P1 · BWD, BoT & To4W' },
        { id: 'p2', label: 'P2 · Firelands' },
        { id: 'p3', label: 'P3 · Dragon Soul' }
      ]
    },
    {
      id: 'mop', label: 'MoP', order: 4,
      phases: [
        { id: 'preraid', label: 'Pre-Raid' },
        { id: 'p1', label: 'P1 · MSV, HoF & ToES' },
        { id: 'p2', label: 'P2 · Throne of Thunder' },
        { id: 'p3', label: 'P3 · Siege of Orgrimmar' }
      ]
    }
  ];

  /* from: first expansion (by order) in which the class/spec exists */
  var CLASSES = [
    { id: 'death-knight', label: 'Death Knight', from: 2, specs: [
      { id: 'blood', label: 'Blood' }, { id: 'frost', label: 'Frost' }, { id: 'unholy', label: 'Unholy' }] },
    { id: 'druid', label: 'Druid', from: 0, specs: [
      { id: 'balance', label: 'Balance' }, { id: 'feral', label: 'Feral' },
      { id: 'guardian', label: 'Guardian', from: 4 }, { id: 'restoration', label: 'Restoration' }] },
    { id: 'hunter', label: 'Hunter', from: 0, specs: [
      { id: 'beast-mastery', label: 'Beast Mastery' }, { id: 'marksmanship', label: 'Marksmanship' }, { id: 'survival', label: 'Survival' }] },
    { id: 'mage', label: 'Mage', from: 0, specs: [
      { id: 'arcane', label: 'Arcane' }, { id: 'fire', label: 'Fire' }, { id: 'frost', label: 'Frost' }] },
    { id: 'monk', label: 'Monk', from: 4, specs: [
      { id: 'brewmaster', label: 'Brewmaster' }, { id: 'mistweaver', label: 'Mistweaver' }, { id: 'windwalker', label: 'Windwalker' }] },
    { id: 'paladin', label: 'Paladin', from: 0, specs: [
      { id: 'holy', label: 'Holy' }, { id: 'protection', label: 'Protection' }, { id: 'retribution', label: 'Retribution' }] },
    { id: 'priest', label: 'Priest', from: 0, specs: [
      { id: 'discipline', label: 'Discipline' }, { id: 'holy', label: 'Holy' }, { id: 'shadow', label: 'Shadow' }] },
    { id: 'rogue', label: 'Rogue', from: 0, specs: [
      { id: 'assassination', label: 'Assassination' }, { id: 'combat', label: 'Combat' }, { id: 'subtlety', label: 'Subtlety' }] },
    { id: 'shaman', label: 'Shaman', from: 0, specs: [
      { id: 'elemental', label: 'Elemental' }, { id: 'enhancement', label: 'Enhancement' }, { id: 'restoration', label: 'Restoration' }] },
    { id: 'warlock', label: 'Warlock', from: 0, specs: [
      { id: 'affliction', label: 'Affliction' }, { id: 'demonology', label: 'Demonology' }, { id: 'destruction', label: 'Destruction' }] },
    { id: 'warrior', label: 'Warrior', from: 0, specs: [
      { id: 'arms', label: 'Arms' }, { id: 'fury', label: 'Fury' }, { id: 'protection', label: 'Protection' }] }
  ];

  var sel = { exp: null, phase: null, cls: null, spec: null };
  var els = {};

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function expById(id) {
    return EXPANSIONS.find(function (e) { return e.id === id; });
  }

  function clsById(id) {
    return CLASSES.find(function (c) { return c.id === id; });
  }

  function wowheadSearch(itemName) {
    var name = itemName.replace(/\s*\((\d+|Legendary)\)\s*$/, '');
    return 'https://www.wowhead.com/' + sel.exp + '/search?q=' + encodeURIComponent(name);
  }

  /* ---------------- picker ---------------- */

  function chip(label, active, onclick) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'bis-chip' + (active ? ' active' : '');
    b.textContent = label;
    b.addEventListener('click', onclick);
    return b;
  }

  function renderPicker() {
    els.expRow.innerHTML = '';
    EXPANSIONS.forEach(function (e) {
      els.expRow.appendChild(chip(e.label, sel.exp === e.id, function () {
        sel.exp = e.id; sel.phase = null;
        var c = clsById(sel.cls);
        if (c && c.from > e.order) { sel.cls = null; sel.spec = null; }
        if (c && sel.spec) {
          var s = c.specs.find(function (x) { return x.id === sel.spec; });
          if (s && (s.from || c.from) > e.order) sel.spec = null;
        }
        update();
      }));
    });

    var exp = expById(sel.exp);
    els.phaseRow.innerHTML = '';
    els.phaseWrap.style.display = exp ? '' : 'none';
    if (exp) {
      exp.phases.forEach(function (p) {
        els.phaseRow.appendChild(chip(p.label, sel.phase === p.id, function () {
          sel.phase = p.id; update();
        }));
      });
    }

    els.classRow.innerHTML = '';
    els.classWrap.style.display = exp ? '' : 'none';
    if (exp) {
      CLASSES.forEach(function (c) {
        if (c.from > exp.order) return;
        els.classRow.appendChild(chip(c.label, sel.cls === c.id, function () {
          if (sel.cls !== c.id) sel.spec = null;
          sel.cls = c.id; update();
        }));
      });
    }

    var cls = clsById(sel.cls);
    els.specRow.innerHTML = '';
    els.specWrap.style.display = exp && cls ? '' : 'none';
    if (exp && cls) {
      cls.specs.forEach(function (s) {
        if ((s.from || cls.from) > exp.order) return;
        els.specRow.appendChild(chip(s.label, sel.spec === s.id, function () {
          sel.spec = s.id; update();
        }));
      });
    }
  }

  /* ---------------- list rendering ---------------- */

  function itemHtml(item, rank) {
    var badge = rank === 0 ? '<span class="rank-badge rank-1">BiS</span>'
      : '<span class="rank-badge">' + (rank + 1) + (rank === 1 ? 'nd' : 'rd') + ' best</span>';
    return '<div class="bis-alt">' + badge +
      '<div class="bis-alt-body">' +
      '<a class="bis-item-name" href="' + wowheadSearch(item.name) + '" target="_blank" rel="noreferrer">' + esc(item.name) + '</a>' +
      '<div class="bis-source">' + esc(item.source || '') + '</div>' +
      '</div></div>';
  }

  function renderList(data) {
    var exp = expById(sel.exp);
    var phase = exp.phases.find(function (p) { return p.id === sel.phase; });
    var cls = clsById(sel.cls);
    var spec = cls.specs.find(function (s) { return s.id === sel.spec; });

    var h = '<div class="bis-list-header">' +
      '<h2>' + esc(spec.label + ' ' + cls.label) + (data.role ? ' <span class="bis-role">' + esc(data.role) + '</span>' : '') + '</h2>' +
      '<div class="bis-list-meta">' + esc(exp.label + ' · ' + phase.label) +
      (data.updated ? ' · Updated ' + esc(data.updated) : '') +
      ' <span class="bis-info-wrap"><button type="button" class="bis-info" aria-label="Report a mistake in this list">i</button>' +
      '<span class="bis-info-pop" role="tooltip">Spotted a mistake in this BiS list? Email ' +
      '<a href="mailto:bis@boostyou.ai">bis@boostyou.ai</a> and we\'ll look into it.</span></span>' +
      '</div>' +
      (data.notes ? '<p class="bis-notes">' + esc(data.notes) + '</p>' : '') +
      '</div>';

    h += '<div class="bis-hint">Click a slot to see the 2nd and 3rd best options. Item names link to Wowhead.</div>';

    h += (data.slots || []).map(function (s) {
      var items = s.items || [];
      if (!items.length) return '';
      var best = items[0];
      var alts = items.slice(1);
      return '<details class="bis-slot">' +
        '<summary>' +
        '<span class="bis-slot-name">' + esc(s.slot) + '</span>' +
        '<span class="bis-slot-item">' +
        '<a class="bis-item-name" href="' + wowheadSearch(best.name) + '" target="_blank" rel="noreferrer">' + esc(best.name) + '</a>' +
        '<span class="bis-source">' + esc(best.source || '') + '</span>' +
        '</span>' +
        '<span class="bis-chevron" aria-hidden="true">▾</span>' +
        '</summary>' +
        '<div class="bis-slot-alts">' +
        (alts.length
          ? alts.map(function (it, i) { return itemHtml(it, i + 1); }).join('')
          : '<div class="bis-source" style="padding:0.25rem 0;">No alternatives listed for this slot.</div>') +
        '</div></details>';
    }).join('');

    if (data.enchants && data.enchants.length) {
      h += '<h3 class="bis-section-title">Enchants</h3><div class="bis-table">' +
        data.enchants.map(function (e) {
          return '<div class="bis-row"><span class="bis-slot-name">' + esc(e.slot) + '</span>' +
            '<span class="bis-slot-item"><span class="bis-item-plain">' + esc(e.name) + '</span>' +
            (e.source ? '<span class="bis-source">' + esc(e.source) + '</span>' : '') +
            '</span></div>';
        }).join('') + '</div>';
    }

    if (data.gems && data.gems.length) {
      h += '<h3 class="bis-section-title">Gems</h3><div class="bis-table">' +
        data.gems.map(function (g) {
          return '<div class="bis-row"><span class="bis-slot-name gem-' + esc(g.color.toLowerCase()) + '">' + esc(g.color) + '</span>' +
            '<span class="bis-slot-item"><span class="bis-item-plain">' + esc(g.name) + '</span></span></div>';
        }).join('') + '</div>';
    }

    els.result.innerHTML = h;
  }

  function renderComingSoon() {
    var exp = expById(sel.exp);
    var cls = clsById(sel.cls);
    var spec = cls.specs.find(function (s) { return s.id === sel.spec; });
    var phase = exp.phases.find(function (p) { return p.id === sel.phase; });
    els.result.innerHTML =
      '<div class="bis-empty">' +
      '<div class="bis-empty-icon">🛠️</div>' +
      '<h2>' + esc(spec.label + ' ' + cls.label) + ' — ' + esc(exp.label + ' ' + phase.label) + '</h2>' +
      '<p>This BiS list isn’t published yet — we’re adding lists phase by phase. ' +
      'In the meantime, <a href="https://www.wowhead.com/' + sel.exp + '/" target="_blank" rel="noreferrer">Wowhead’s ' + esc(exp.label) + ' guides</a> have you covered.</p>' +
      '<p class="bis-empty-nudge">Subscribe below and we’ll mail you when new lists go live.</p>' +
      '</div>';
  }

  function renderPrompt() {
    var msg = !sel.exp ? 'Pick an expansion to get started.'
      : !sel.phase ? 'Pick a phase.'
      : !sel.cls ? 'Pick a class.'
      : 'Pick a specialization.';
    els.result.innerHTML = '<div class="bis-empty"><div class="bis-empty-icon">🧭</div><p>' + msg + '</p></div>';
  }

  /* ---------------- state ---------------- */

  function update(skipHash) {
    renderPicker();
    if (!skipHash) {
      var parts = [sel.exp, sel.phase, sel.cls, sel.spec].filter(Boolean);
      var newHash = parts.length ? '#' + parts.join('/') : '';
      if (('#' + parts.join('/')) !== location.hash) {
        history.replaceState(null, '', newHash || location.pathname + location.search);
      }
    }
    if (sel.exp && sel.phase && sel.cls && sel.spec) {
      els.result.innerHTML = '<div class="bis-empty"><p>Loading…</p></div>';
      var file = DATA_BASE + [sel.exp, sel.phase, sel.cls, sel.spec].join('-') + '.json';
      fetch(file)
        .then(function (r) {
          if (!r.ok) throw new Error(String(r.status));
          return r.json();
        })
        .then(renderList)
        .catch(renderComingSoon);
    } else {
      renderPrompt();
    }
  }

  function readHash() {
    var parts = location.hash.replace(/^#/, '').split('/').filter(Boolean);
    sel.exp = parts[0] && expById(parts[0]) ? parts[0] : null;
    var exp = expById(sel.exp);
    sel.phase = sel.exp && parts[1] && exp.phases.some(function (p) { return p.id === parts[1]; }) ? parts[1] : null;
    sel.cls = parts[2] && clsById(parts[2]) ? parts[2] : null;
    var cls = clsById(sel.cls);
    sel.spec = sel.cls && parts[3] && cls.specs.some(function (s) { return s.id === parts[3]; }) ? parts[3] : null;
  }

  document.addEventListener('DOMContentLoaded', function () {
    ['expRow', 'phaseRow', 'classRow', 'specRow', 'phaseWrap', 'classWrap', 'specWrap', 'result'].forEach(function (id) {
      els[id] = document.getElementById(id);
    });
    if (!els.result) return;
    readHash();
    update(true);
    window.addEventListener('hashchange', function () {
      readHash();
      update(true);
    });
  });
})();
